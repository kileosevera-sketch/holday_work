import { Brain, Cpu, FileText, Layers, Sparkles, TrendingUp } from 'lucide-react';

function AIInsights({ predictions = [], feedback = [] }) {
  const total = predictions.reduce((sum, item) => sum + item.count, 0);
  const recentEvidence = feedback.slice(0, 8);

  return (
    <div className="mx-auto max-w-7xl space-y-7">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#965228]">
          Objective 5, 6 & 7 · Explainable AI & Failure Prediction
        </p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900 sm:text-3xl">
          Root-Cause Predictions & Evidence
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          Ranked failure causes, probability likelihood scores, and clear contributing factors extracted from post-sales feedback.
        </p>
      </header>

      {/* CLASSIFICATION ENGINE METRICS */}
      <section className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center gap-3.5">
          <span className="rounded-xl bg-[#E8EFEA] p-3 text-[#354E4B]">
            <Brain className="h-6 w-6" />
          </span>
          <div>
            <h2 className="font-bold text-slate-900">Probabilistic Root-Cause Inference Engine</h2>
            <p className="text-xs text-slate-500">Bayesian Softmax Likelihood · Symptom-to-Failure Correlation</p>
          </div>
        </div>
        <div className="flex gap-6 text-sm">
          <div>
            <p className="text-xs text-slate-400">Total Analyzed Records</p>
            <p className="text-lg font-bold text-slate-900">{total.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-slate-400">Emerging Failure Patterns</p>
            <p className="text-lg font-bold text-[#6F4530]">{predictions.length} Categories</p>
          </div>
        </div>
      </section>

      {/* RANKED CAUSE CARDS */}
      <section>
        <div className="mb-3">
          <h2 className="text-base font-bold text-slate-900">Ranked Failure Cause Distributions & Future Likelihood</h2>
          <p className="text-xs text-slate-500">Likelihood of failure recurrence based on historical patterns</p>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {predictions.map((item, index) => {
            const pct = total ? (item.count / total) * 100 : 0;
            const isHighRisk = pct > 20 || index < 2;

            return (
              <article key={item.cause} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <span className="rounded-lg bg-[#F1F6F1] p-2 text-[#354E4B]">
                      <Layers className="h-5 w-5" />
                    </span>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-[#52706A]">
                        Rank {index + 1}
                      </p>
                      <h3 className="mt-0.5 text-base font-bold text-slate-900">
                        {item.cause.replaceAll('_', ' ')}
                      </h3>
                    </div>
                  </div>
                  <span className="shrink-0 rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-800">
                    {item.count} records ({pct.toFixed(1)}%)
                  </span>
                </div>

                {/* Progress bar */}
                <div className="mt-4 h-2.5 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.max(5, pct)}%`,
                      backgroundColor: index === 0 ? '#6F4530' : index === 1 ? '#C08A5B' : '#52706A',
                    }}
                  />
                </div>

                <div className="mt-3 flex items-center justify-between text-xs">
                  <span className="text-slate-500">
                    Proportion of all customer complaints
                  </span>
                  <span className={`font-semibold inline-flex items-center gap-1 ${isHighRisk ? 'text-amber-800' : 'text-slate-600'}`}>
                    <TrendingUp className="h-3.5 w-3.5" />
                    {isHighRisk ? 'High Recurrence Risk' : 'Moderate Recurrence Risk'}
                  </span>
                </div>
              </article>
            );
          })}

          {!predictions.length && (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center lg:col-span-2">
              <Sparkles className="mx-auto h-8 w-8 text-[#52706A]" />
              <p className="mt-3 font-semibold text-slate-800">No failure patterns inferred yet</p>
              <p className="mt-1 text-xs text-slate-500">Upload customer feedback files to train the failure prediction model.</p>
            </div>
          )}
        </div>
      </section>

      {/* EVIDENCE & CONTRIBUTING FACTORS */}
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2.5">
            <FileText className="h-5 w-5 text-[#52706A]" />
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Explainable AI: Evidence & Contributing Factors</h2>
              <p className="text-xs text-slate-500">Direct customer quotes supporting the inferred root causes</p>
            </div>
          </div>
          <span className="text-xs font-semibold text-slate-500">Verified Evidence</span>
        </div>

        <div className="divide-y divide-slate-100">
          {recentEvidence.map((row) => (
            <article key={row.id} className="py-4">
              <p className="text-sm font-medium text-slate-800 leading-relaxed">
                "{row.feedback_text}"
              </p>

              <div className="mt-2.5 flex flex-wrap items-center gap-2 text-xs">
                <span className="rounded-md bg-[#F1F6F1] px-2.5 py-1 font-semibold text-[#354E4B]">
                  Root Cause: {row.predicted_cause}
                </span>

                {row.prediction_confidence > 0 && (
                  <span className="rounded-md bg-slate-100 px-2 py-1 font-bold text-slate-700">
                    {row.prediction_confidence}% Confidence
                  </span>
                )}

                <span className={`rounded-md px-2 py-1 font-semibold uppercase ${
                  row.severity === 'critical' ? 'bg-rose-800 text-white' :
                  row.severity === 'high' ? 'bg-orange-600 text-white' :
                  'bg-slate-100 text-slate-700'
                }`}>
                  {row.severity}
                </span>

                {/* Display Contributing Factors */}
                {Array.isArray(row.contributing_factors) && row.contributing_factors.map((factor) => (
                  <span key={factor} className="rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] text-amber-900">
                    Factor: {factor}
                  </span>
                ))}
              </div>
            </article>
          ))}

          {!recentEvidence.length && (
            <p className="py-10 text-center text-sm text-slate-500">
              Supporting customer complaint evidence will appear here after upload.
            </p>
          )}
        </div>

        <div className="mt-5 flex items-center gap-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
          <Cpu className="h-4 w-4 shrink-0 text-[#6F4530]" />
          Explainable AI links customer vernacular with known hardware/software defect signatures to prevent recurring failures.
        </div>
      </section>
    </div>
  );
}

export default AIInsights;
