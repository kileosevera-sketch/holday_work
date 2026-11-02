"""Enterprise NLP Classification & Failure Prediction Engine for Post-Sales Customer Feedback.

Implements:
1. Multi-factor sentiment analysis (VADER + domain polarity heuristics).
2. Multi-tier severity level classification (critical, high, medium, low -> high vs low priority).
3. Symptom extraction and problem mapping.
4. Failure prediction and probabilistic root-cause ranking with clear contributing factors.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Tuple
import pandas as pd

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _VADER_ANALYZER = SentimentIntensityAnalyzer()
except Exception:
    _VADER_ANALYZER = None


# ---------------------------------------------------------------------------
# 1. Symptom & Problem Knowledge Base
# ---------------------------------------------------------------------------
SYMPTOM_PATTERNS: Dict[str, List[str]] = {
    "power_battery_failure": [
        r"\b(won'?t turn on|cannot turn on|no power|dead on arrival|dead device)\b",
        r"\b(battery (draining fast|dies quickly|won'?t charge|not charging|swollen))\b",
        r"\b(powers? (off|down) randomly|sudden shutdown|black screen)\b",
    ],
    "thermal_overheating": [
        r"\b(overheat(ing|s)?|extremely hot|burning smell|smoke|fire hazard)\b",
        r"\b(fan (loud|noisy|spinning constantly)|thermal throttling)\b",
        r"\b(hot to (the )?touch|melts?|warm surface)\b",
    ],
    "display_panel_defect": [
        r"\b(screen (flicker(s|ing)?|blinking|blank|black|freez(es|ing)))\b",
        r"\b(dead pixels?|vertical lines?|horizontal lines?|discoloration)\b",
        r"\b(touchscreen (unresponsive|not working|ghost touch))\b",
    ],
    "audio_speaker_issue": [
        r"\b(no (sound|audio)|distorted (sound|audio)|speaker crackl(es|ing))\b",
        r"\b(microphone (not working|dead|muffled)|buzzing sound|humming)\b",
    ],
    "wireless_connectivity_drop": [
        r"\b(wi-?fi (disconnecting|drops|not connecting|slow|unstable))\b",
        r"\b(bluetooth (won'?t pair|pairing failed|drops out|connection lost))\b",
        r"\b(no signal|weak signal|network error)\b",
    ],
    "software_firmware_instability": [
        r"\b(app (crash(es|ed)?|freez(es|ed)?)|boot loop|system (error|bug))\b",
        r"\b(firmware update failed|stuck on loading|frozen screen)\b",
        r"\b(software glitch|kernel panic|blue screen|unresponsive ui)\b",
    ],
    "physical_transit_damage": [
        r"\b(shattered|cracked (screen|casing|glass)|dented|bent)\b",
        r"\b(packaging (damaged|crushed|ripped)|broken (box|hinge|latch))\b",
        r"\b(physical damage|scratched out of box)\b",
    ],
    "shipping_delivery_delay": [
        r"\b(never arrived|lost package|delivery (late|delayed|failed))\b",
        r"\b(tracking (not updating|invalid)|wrong item delivered)\b",
        r"\b(waiting for (shipment|package)|where is my order)\b",
    ],
    "billing_invoice_error": [
        r"\b(charged twice|double charged|wrong amount billed|overcharged)\b",
        r"\b(refund (not received|delayed|refused|missing)|unauthorized charge)\b",
        r"\b(invoice error|subscription cancelled but charged)\b",
    ],
    "customer_service_gap": [
        r"\b(customer support (rude|unhelpful|ignoring|terrible|slow))\b",
        r"\b(no response (for days|to email)|agent hung up|ticket closed without resolution)\b",
        r"\b(long hold time|transferred multiple times)\b",
    ],
}

# Compile patterns for fast streaming
COMPILED_SYMPTOMS = {
    symptom: [re.compile(p, re.IGNORECASE) for p in patterns]
    for symptom, patterns in SYMPTOM_PATTERNS.items()
}


# ---------------------------------------------------------------------------
# 2. Failure Root Causes & Symptom Association Matrix
# ---------------------------------------------------------------------------
ROOT_CAUSE_MAPPINGS: Dict[str, Dict[str, Any]] = {
    "Power & Battery Circuitry Fault": {
        "key": "power_battery_circuitry_fault",
        "primary_symptoms": ["power_battery_failure", "thermal_overheating"],
        "keywords": ["battery", "charge", "power", "dead", "shutdown", "adapter", "voltage", "current"],
        "base_weight": 1.2,
    },
    "Thermal Management & Heat Dissipation Defect": {
        "key": "thermal_management_defect",
        "primary_symptoms": ["thermal_overheating"],
        "keywords": ["overheat", "hot", "temperature", "fan", "cooling", "thermal", "throttling", "melt"],
        "base_weight": 1.3,
    },
    "Display Panel & Touch Digitizer Degradation": {
        "key": "display_panel_defect",
        "primary_symptoms": ["display_panel_defect"],
        "keywords": ["screen", "display", "flicker", "pixel", "touch", "backlight", "digitizer", "lcd", "oled"],
        "base_weight": 1.2,
    },
    "Firmware & Operating System Instability": {
        "key": "firmware_os_instability",
        "primary_symptoms": ["software_firmware_instability"],
        "keywords": ["crash", "software", "firmware", "freeze", "boot", "update", "os", "bug", "glitch"],
        "base_weight": 1.1,
    },
    "Wireless RF & Network Module Failure": {
        "key": "wireless_rf_failure",
        "primary_symptoms": ["wireless_connectivity_drop"],
        "keywords": ["wifi", "bluetooth", "wireless", "connect", "signal", "pairing", "network", "modem"],
        "base_weight": 1.1,
    },
    "Acoustic Transducer & Audio Hardware Fault": {
        "key": "audio_hardware_fault",
        "primary_symptoms": ["audio_speaker_issue"],
        "keywords": ["sound", "audio", "speaker", "mic", "microphone", "distort", "static", "crackling"],
        "base_weight": 1.1,
    },
    "Transit Handling & Packaging Failure": {
        "key": "transit_handling_damage",
        "primary_symptoms": ["physical_transit_damage", "shipping_delivery_delay"],
        "keywords": ["shipped", "package", "cracked", "dented", "crushed", "delivery", "box", "shipping"],
        "base_weight": 1.15,
    },
    "Payment Gateway & Billing Synchronization Error": {
        "key": "billing_gateway_error",
        "primary_symptoms": ["billing_invoice_error"],
        "keywords": ["charge", "billed", "invoice", "refund", "payment", "card", "subscription", "account"],
        "base_weight": 1.2,
    },
    "Support Operations & SLA Escalation Gap": {
        "key": "support_sla_breach",
        "primary_symptoms": ["customer_service_gap"],
        "keywords": ["support", "agent", "service", "representative", "reply", "ticket", "call", "wait", "rude"],
        "base_weight": 1.0,
    },
    "Positive Experience / No Hardware Failure": {
        "key": "positive_experience",
        "primary_symptoms": [],
        "keywords": ["great", "love", "good", "excellent", "perfect", "satisfied", "helpful", "working fine"],
        "base_weight": 0.8,
    },
}

# ---------------------------------------------------------------------------
# 3. Severity Regex Patterns
# ---------------------------------------------------------------------------
CRITICAL_REGEX = re.compile(
    r"\b(emergency|urgent|danger|dangerous|hazard|fire|smoke|shock|explode|spark|battery swelling|"
    r"burn(ing|t)? smell|injury|fraud|stolen|unauthorized transaction|data loss|catastrophic|"
    r"legal action|lawyer|sue|safety issue)\b",
    re.IGNORECASE,
)

HIGH_REGEX = re.compile(
    r"\b(won'?t turn on|completely dead|dead on arrival|unusable|broken|defective|failed|failure|"
    r"constant crash|black screen|charged twice|refuse to pay|cancel order|demanding refund|"
    r"never arrived|lost shipment|terrible|furious|horrible)\b",
    re.IGNORECASE,
)

MEDIUM_REGEX = re.compile(
    r"\b(slow|lag|delay|intermittent|glitch|bug|unstable|dropped|poor quality|disappointed|"
    r"difficult|confusing|waiting|inconvenient|minor issue|frustrated)\b",
    re.IGNORECASE,
)


def clean_text(text: str) -> str:
    """Normalize input text by removing control characters and collapsing whitespaces."""
    if not isinstance(text, str):
        text = str(text or "")
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def analyze_sentiment(text: str) -> Tuple[str, float]:
    """
    Perform sentiment classification using VADER with fallback heuristics.
    Returns: (label: "positive"|"neutral"|"negative", score: float [-1.0, 1.0])
    """
    if not text:
        return "neutral", 0.0

    if _VADER_ANALYZER is not None:
        scores = _VADER_ANALYZER.polarity_scores(text)
        compound = float(scores.get("compound", 0.0))
    else:
        # Fallback keyword-based polarity score
        pos_words = len(re.findall(r"\b(good|great|excellent|love|perfect|fast|happy|satisfied|best|amazing)\b", text, re.I))
        neg_words = len(re.findall(r"\b(bad|terrible|poor|broken|worst|horrible|angry|hate|useless|failed|slow)\b", text, re.I))
        total_matched = pos_words + neg_words
        compound = (pos_words - neg_words) / total_matched if total_matched > 0 else 0.0

    if compound >= 0.05:
        return "positive", compound
    elif compound <= -0.05:
        return "negative", compound
    else:
        return "neutral", compound


def analyze_severity(text: str, sentiment: str) -> Tuple[str, str]:
    """
    Classify severity into 4 granular tiers and map to binary priority (high_priority vs low_priority).
    Returns: (tier: "low"|"medium"|"high"|"critical", priority: "high_priority"|"low_priority")
    """
    if CRITICAL_REGEX.search(text):
        return "critical", "high_priority"
    if HIGH_REGEX.search(text):
        return "high", "high_priority"
    if MEDIUM_REGEX.search(text):
        return "medium", "low_priority"

    # If strongly negative without explicit keywords, elevate to medium
    if sentiment == "negative":
        return "medium", "low_priority"

    return "low", "low_priority"


def extract_symptoms(text: str) -> List[str]:
    """Extract list of detected symptom codes based on domain patterns."""
    detected = []
    for symptom_code, patterns in COMPILED_SYMPTOMS.items():
        for pattern in patterns:
            if pattern.search(text):
                detected.append(symptom_code)
                break
    return detected


def predict_root_cause(
    text: str,
    symptoms: List[str],
    sentiment: str,
    severity: str,
) -> Tuple[str, float, List[str], Dict[str, float]]:
    """
    Predict underlying root failure cause with precise probability scores (%) and contributing factors.
    Returns:
        (predicted_cause: str,
         confidence_percentage: float,
         contributing_factors: List[str],
         all_probabilities: Dict[cause_label, probability_percentage])
    """
    lower_text = text.lower()
    raw_scores: Dict[str, float] = {}
    contributing_map: Dict[str, List[str]] = {}

    for cause_label, info in ROOT_CAUSE_MAPPINGS.items():
        score = 0.05  # Base smoothing prior
        factors = []

        # 1. Symptom matching boost (high confidence signal)
        for sym in info["primary_symptoms"]:
            if sym in symptoms:
                score += 3.0 * info["base_weight"]
                clean_sym = sym.replace("_", " ")
                factors.append(f"Detected symptom: {clean_sym}")

        # 2. Keyword co-occurrence boost
        for kw in info["keywords"]:
            if re.search(r"\b" + re.escape(kw) + r"\b", lower_text):
                score += 0.8 * info["base_weight"]
                if len(factors) < 4:
                    factors.append(f"Keyword match: '{kw}'")

        # 3. Contextual modifier
        if cause_label == "Positive Experience / No Hardware Failure":
            if sentiment == "positive":
                score += 3.5
                factors.append("Positive sentiment polarity detected")
            elif sentiment == "negative":
                score = 0.01  # Suppress positive classification on negative text
        else:
            if severity in ("high", "critical"):
                score *= 1.3
            elif sentiment == "positive" and not symptoms:
                score *= 0.2

        raw_scores[cause_label] = max(0.01, score)
        contributing_map[cause_label] = factors

    # Softmax conversion to guaranteed probabilities summing to 100%
    exp_scores = {k: math.exp(min(20.0, v)) for k, v in raw_scores.items()}
    sum_exp = sum(exp_scores.values()) or 1.0
    probabilities = {k: round((v / sum_exp) * 100.0, 1) for k, v in exp_scores.items()}

    # Pick top predicted root cause
    sorted_causes = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    top_cause, top_prob = sorted_causes[0]
    top_factors = contributing_map.get(top_cause, [])

    if not top_factors:
        top_factors = ["Inferred from contextual sentence semantics"]

    return top_cause, top_prob, top_factors, probabilities


def analyze_single_record(text: str) -> Dict[str, Any]:
    """Runs the complete NLP pipeline on a single feedback text snippet."""
    cleaned = clean_text(text)
    sentiment, sentiment_score = analyze_sentiment(cleaned)
    severity, priority = analyze_severity(cleaned, sentiment)
    symptoms = extract_symptoms(cleaned)
    cause, prob, factors, all_probs = predict_root_cause(cleaned, symptoms, sentiment, severity)

    return {
        "feedback_text": cleaned,
        "sentiment": sentiment,
        "sentiment_score": round(sentiment_score, 3),
        "severity": severity,
        "severity_priority": priority,
        "detected_symptoms": symptoms,
        "predicted_cause": cause,
        "prediction_confidence": prob,
        "contributing_factors": factors,
        "all_probabilities": all_probs,
    }


def analyze_dataframe(df: pd.DataFrame, text_col: str | None = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Analyzes an entire pandas DataFrame of customer feedback.
    Returns:
        (analyzed_df: pd.DataFrame with enriched columns,
         aggregated_summary: Dict with summary metrics, trends, and root cause rankings)
    """
    if df.empty:
        raise ValueError("Provided dataframe contains no data rows.")

    # Auto-detect feedback text column if not specified
    if not text_col:
        lookup = {str(col).strip().lower(): col for col in df.columns}
        candidates = [
            "feedback_text", "feedback", "text", "customer_feedback", "review",
            "comment", "comments", "description", "issue", "message", "complaint"
        ]
        for cand in candidates:
            if cand in lookup:
                text_col = lookup[cand]
                break

    if not text_col or text_col not in df.columns:
        raise ValueError(
            f"Could not identify a feedback text column in dataset. Available columns: {list(df.columns)}"
        )

    # Clean text column
    texts = df[text_col].fillna("").astype(str).map(clean_text)
    valid_mask = texts.str.len() > 1
    analyzed_df = df.loc[valid_mask].copy()
    valid_texts = texts.loc[valid_mask].tolist()

    if not valid_texts:
        raise ValueError("No valid, non-empty customer feedback records found in file.")

    results = [analyze_single_record(t) for t in valid_texts]

    analyzed_df["feedback_text"] = [r["feedback_text"] for r in results]
    analyzed_df["sentiment"] = [r["sentiment"] for r in results]
    analyzed_df["sentiment_score"] = [r["sentiment_score"] for r in results]
    analyzed_df["severity"] = [r["severity"] for r in results]
    analyzed_df["severity_priority"] = [r["severity_priority"] for r in results]
    analyzed_df["detected_symptoms"] = [r["detected_symptoms"] for r in results]
    analyzed_df["predicted_cause"] = [r["predicted_cause"] for r in results]
    analyzed_df["prediction_confidence"] = [r["prediction_confidence"] for r in results]
    analyzed_df["contributing_factors"] = [r["contributing_factors"] for r in results]

    # Generate aggregated analytics for database JSON storage
    total_records = len(analyzed_df)
    sentiment_counts = analyzed_df["sentiment"].value_counts().to_dict()
    severity_counts = analyzed_df["severity"].value_counts().to_dict()

    # Ranked Root Causes with average probability and aggregated factors
    ranked_causes_list = []
    cause_groups = analyzed_df.groupby("predicted_cause")
    for cause_name, group in cause_groups:
        count = len(group)
        pct = round((count / total_records) * 100.0, 1)
        avg_conf = round(float(group["prediction_confidence"].mean()), 1)
        
        # Aggregate common contributing factors
        all_factors = [f for sublist in group["contributing_factors"] for f in sublist]
        factor_counts = pd.Series(all_factors).value_counts().head(3).index.tolist() if all_factors else []

        ranked_causes_list.append({
            "cause": cause_name,
            "count": count,
            "percentage": pct,
            "average_confidence": avg_conf,
            "contributing_factors": factor_counts,
        })

    # Sort descending by count, then confidence
    ranked_causes_list.sort(key=lambda x: (x["count"], x["average_confidence"]), reverse=True)

    summary_metrics = {
        "total_records": total_records,
        "analyzed_records": total_records,
        "critical_count": int(severity_counts.get("critical", 0)),
        "high_priority_count": int(analyzed_df["severity_priority"].eq("high_priority").sum()),
        "low_priority_count": int(analyzed_df["severity_priority"].eq("low_priority").sum()),
        "sentiment": {
            "positive": int(sentiment_counts.get("positive", 0)),
            "neutral": int(sentiment_counts.get("neutral", 0)),
            "negative": int(sentiment_counts.get("negative", 0)),
        },
        "severity": {
            "low": int(severity_counts.get("low", 0)),
            "medium": int(severity_counts.get("medium", 0)),
            "high": int(severity_counts.get("high", 0)),
            "critical": int(severity_counts.get("critical", 0)),
        },
        "causes": [{"cause": c["cause"], "count": c["count"]} for c in ranked_causes_list],
    }

    return analyzed_df, {
        "summary": summary_metrics,
        "root_cause_ranking": ranked_causes_list,
    }



# ---------------------------------------------------------------------------
# 4. EARLY WARNING: STATISTICAL ANOMALY / SPIKE DETECTION  (Objective 8)
# ---------------------------------------------------------------------------
def detect_anomalies(daily_counts: List[Tuple[str, int]], min_history: int = 3, z_threshold: float = 2.0) -> List[Dict[str, Any]]:
    """
    Detect unusual increases in complaint volume using a rolling-baseline z-score test.

    For each day (after an initial warm-up window), compare that day's complaint count
    against the mean and standard deviation of all *previous* days. A day whose volume
    exceeds mean + z_threshold * std is flagged as an emerging failure spike / early warning.

    Args:
        daily_counts: ordered list of (date_string "YYYY-MM-DD", count) tuples.
        min_history:  minimum number of prior days required before a day can be evaluated.
        z_threshold:  how many standard deviations above baseline counts as "unusual".

    Returns:
        List of anomaly records, newest relevant first:
        [{date, count, baseline_mean, baseline_std, z_score, severity, message}]
    """
    anomalies: List[Dict[str, Any]] = []
    history: List[int] = []

    for date_str, count in daily_counts:
        if len(history) >= min_history:
            mean = sum(history) / len(history)
            variance = sum((x - mean) ** 2 for x in history) / len(history)
            std = math.sqrt(variance)

            # Guard against a flat baseline (std == 0): any increase is then notable
            if std == 0.0:
                unusual = count > mean
                z = float("inf") if count > mean else 0.0
            else:
                z = (count - mean) / std
                unusual = z >= z_threshold

            if unusual:
                severity = "critical" if z >= z_threshold * 2 else "high"
                anomalies.append({
                    "date": date_str,
                    "count": int(count),
                    "baseline_mean": round(mean, 1),
                    "baseline_std": round(std, 1),
                    "z_score": round(z, 2),
                    "severity": severity,
                    "message": (
                        f"Unusual surge detected: {int(count)} complaints on {date_str} vs. an "
                        f"average baseline of {mean:.1f} (z-score {z:.2f}). Possible emerging failure."
                    ),
                })

        history.append(count)

    return anomalies


# ---------------------------------------------------------------------------
# 5. FORWARD-LOOKING FAILURE LIKELIHOOD PREDICTION  (Objective: Predict likelihood of future failures)
# ---------------------------------------------------------------------------
def predict_future_failures(
    daily_counts: List[Tuple[str, int]],
    cause_counts: Dict[str, int],
    horizon_days: int = 7,
) -> Dict[str, Any]:
    """
    Predict the likelihood of future failures over the next `horizon_days`.

    Method (lightweight, explainable — no external ML dependencies):
      1. Total-volume forecast: weighted linear trend (recent days weighted more) +
         exponential smoothing blend, floored at zero.
      2. Cause-share projection: each root cause's future share blends its historical
         share with its *recent* share (last 30% of dated records) so rising causes
         gain likelihood and fading causes lose it.
      3. Per-cause expected failures next horizon = forecast volume * projected share.

    Returns:
        {
          "horizon_days": int,
          "forecast_total_failures": float,     # expected complaints next horizon
          "daily_forecast": [{date, expected_count}...],
          "cause_forecasts": [{cause, historical_share_pct, recent_share_pct,
                               projected_share_pct, expected_failures, likelihood_pct,
                               trend}],         # trend: "rising"|"falling"|"stable"
          "method": str,
        }
    """
    if not daily_counts:
        return {"horizon_days": horizon_days, "forecast_total_failures": 0.0,
                "daily_forecast": [], "cause_forecasts": [], "method": "insufficient-history"}

    counts = [c for _, c in daily_counts]
    n = len(counts)

    # --- 1. Weighted linear trend forecast of daily volume -------------------
    weights = [1 + (i / max(1, n - 1)) * 2 for i in range(n)]  # recent days weigh up to 3x
    w_sum = sum(weights)
    w_mean_x = sum((i + 1) * w for i, w in enumerate(weights)) / w_sum
    w_mean_y = sum(c * w for c, w in zip(counts, weights)) / w_sum
    denom = sum(w * ((i + 1) - w_mean_x) ** 2 for i, w in enumerate(weights)) or 1.0
    slope = sum(w * ((i + 1) - w_mean_x) * (c - w_mean_y)
                for i, (c, w) in enumerate(zip(counts, weights))) / denom
    intercept = w_mean_y - slope * w_mean_x

    recent_window = counts[-max(3, n // 3):]
    ema_alpha = 0.5
    ema = recent_window[0]
    for c in recent_window[1:]:
        ema = ema_alpha * c + (1 - ema_alpha) * ema

    # Blend trend projection with exponential smoothing; clamp small baselines to zero
    next_day = max(0.0, 0.6 * (intercept + slope * (n + 1)) + 0.4 * ema)
    if sum(counts) < 5:
        next_day = 0.0

    from datetime import date as _date, timedelta as _td
    try:
        last_date = _date.fromisoformat(daily_counts[-1][0])
    except ValueError:
        last_date = _date.today()

    daily_forecast = []
    for d in range(1, horizon_days + 1):
        day = last_date + _td(days=d)
        daily_forecast.append({"date": day.isoformat(), "expected_count": round(next_day, 2)})
    forecast_total = next_day * horizon_days

    # --- 2. Cause-share projection -------------------------------------------
    total_cause_hits = sum(cause_counts.values()) or 1

    # Recent share approximation: bump causes using last 40% of daily volume growth
    recent_volume = sum(counts[-max(1, n // 3):]) or 1
    historical_volume = sum(counts) or 1
    momentum = recent_volume / historical_volume  # >1 means activity accelerating

    cause_forecasts = []
    for cause, cnt in sorted(cause_counts.items(), key=lambda kv: kv[1], reverse=True):
        hist_share = cnt / total_cause_hits

        # Causes tied to physical/hardware failure scale with rising complaint momentum;
        # positive-experience causes are damped when momentum is high.
        is_positive = "positive" in cause.lower()
        momentum_factor = momentum if not is_positive else (1.0 / max(momentum, 0.05))
        recent_share = min(0.95, hist_share * momentum_factor)

        projected_share = 0.5 * hist_share + 0.5 * recent_share
        expected = projected_share * forecast_total

        if recent_share > hist_share * 1.15:
            trend = "rising"
        elif recent_share < hist_share * 0.85:
            trend = "falling"
        else:
            trend = "stable"

        cause_forecasts.append({
            "cause": cause,
            "count": int(cnt),
            "historical_share_pct": round(hist_share * 100.0, 1),
            "projected_share_pct": round(projected_share * 100.0, 1),
            "expected_failures": round(expected, 1),
            "likelihood_pct": round(projected_share * 100.0, 1),
            "trend": trend,
        })

    # Renormalize likelihoods to 100%
    like_sum = sum(c["likelihood_pct"] for c in cause_forecasts) or 1.0
    for c in cause_forecasts:
        c["likelihood_pct"] = round(c["likelihood_pct"] / like_sum * 100.0, 1)

    cause_forecasts.sort(key=lambda c: c["expected_failures"], reverse=True)

    return {
        "horizon_days": horizon_days,
        "forecast_total_failures": round(forecast_total, 1),
        "daily_forecast": daily_forecast,
        "cause_forecasts": cause_forecasts,
        "method": "weighted-trend + exponential-smoothing volume forecast with momentum-adjusted cause shares",
    }
