"""NLP and lightweight machine-learning feedback classification pipeline."""
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

_sentiment_examples = [
    ("excellent fast helpful wonderful happy satisfied great service thank you love it resolved", "positive"),
    ("fine okay acceptable working as expected average nothing special", "neutral"),
    ("bad broken terrible disappointed angry unusable slow poor failed never works frustrated", "negative"),
]
_cause_examples = [
    ("app crashes freezes error loading login software bug", "software_issue"),
    ("payment charged billing invoice refund transaction", "billing_payment"),
    ("delivery late shipping package order tracking", "delivery_logistics"),
    ("support agent call response rude customer service", "customer_support"),
    ("product damaged defective quality broken item", "product_quality"),
    ("cannot find feature confusing instructions setup", "usability"),
    ("excellent fast helpful satisfied", "positive_experience"),
]

def _train_classifier(examples):
    model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
        LogisticRegression(max_iter=500, random_state=17))
    model.fit([text for text, _ in examples], [label for _, label in examples])
    return model

_sentiment_model = _train_classifier(_sentiment_examples)
_cause_model = _train_classifier(_cause_examples)
_critical_terms = re.compile(r"\b(urgent|emergency|unsafe|injury|fraud|stolen|outage|data loss|charged twice|critical)\b", re.I)
_high_terms = re.compile(r"\b(broken|failed|failure|crash|unusable|refund|complaint|angry|cancel|error|defective)\b", re.I)
_medium_terms = re.compile(r"\b(slow|late|issue|problem|difficult|confusing|disappointed)\b", re.I)

def _classify_severity(text: str) -> str:
    if _critical_terms.search(text):
        return "critical"
    if _high_terms.search(text):
        return "high"
    if _medium_terms.search(text):
        return "medium"
    return "low"

def analyze_feedback(data: pd.DataFrame, text_column: str | None = None) -> pd.DataFrame:
    """Return non-empty feedback rows with sentiment, severity, and cause predictions."""
    if data.empty:
        raise ValueError("The uploaded CSV contains no data rows.")
    if text_column is None:
        columns = {str(column).strip().lower(): column for column in data.columns}
        for candidate in ("feedback_text", "feedback", "text", "comment", "review", "message"):
            if candidate in columns:
                text_column = columns[candidate]
                break
    if text_column is None or text_column not in data.columns:
        raise ValueError("CSV needs a text column named feedback_text, feedback, text, comment, review, or message.")
    texts = data[text_column].fillna("").astype(str).str.strip()
    valid = texts.ne("")
    if not valid.any():
        raise ValueError("No non-empty feedback text was found in the CSV.")
    result = data.loc[valid].copy()
    texts = texts.loc[valid]
    result["feedback_text"] = texts
    result["sentiment"] = _sentiment_model.predict(texts.tolist())
    result["severity"] = [_classify_severity(text) for text in texts]
    result["predicted_cause"] = _cause_model.predict(texts.tolist())
    return result.reset_index(drop=True)
