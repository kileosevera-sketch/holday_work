import { useState } from 'react';
import { analyzePendingFeedback } from '../api';
import { ShieldAlert, Tags } from 'lucide-react';

const MetricCard = ({ label, count, total, color, helper }) => {
  const percent = total ? Math.round((count / total) * 100) : 0;
  return (
    <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex justify-between text-sm font-semibold text-slate-800">
        <span>{label}</span>
        <span>{percent}%</span>
      </div>
      <p className="text-3xl font-bold text-slate-900">{Number(count || 0).toLocaleString()}</p>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${percent}%`, backgroundColor: color }} />
      </div>
      <p className="text-xs text-slate-500">{helper}</p>
    </div>
  );
};

function Analysis({ summary = {}, feedback = [], onRefresh }) {
  const [running, setRunning] = useState(false);
  const [analysisMessage, setAnalysisMessage] = useState('');
  const [analysisError, setAnalysisError] = useState('');

  const total = Number(summary.analyzed_feedback || 0);
  const analyzed = Number(summary.analyzed_feedback || 0);
  const pending = Number(summary.pending_analysis || 0);
  const sentiment = summary.sentiment || {};
  const severity = summary.severity || {};
  const causes = summary.causes || [];

  const runAnalysis = async () => {
    setRunning(true);
    setAnalysisMessage('');
    setAnalysisError('');
    try {
      const result = await analyzePendingFeedback();
      setAnalysisMessage(`${result.analyzed} records analyzed using ${result.analysis_method}.`);
      await onRefresh?.();
    } catch (error) {
      setAnalysisError(error.message || 'Analysis failed. Check backend connection.');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl space-y-7">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#52706A]">
          Objective 1 & 2 · AI Post-Sales Ingestion
        </p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900 sm:text-3xl">
          Feedback Classification & Failure Analysis
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          NLP classification of customer feedback, linking customer symptoms with technical failure causes.
        </p>
      </header>

      {/* ANALYSIS STATUS BANNER */}
      <section className="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-[#354E4B] p-6 text-white shadow-sm">
        <div>
          <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold tracking-wider">
            {analyzed.toLocaleString()} OF {Number(summary.total_feedback || 0).toLocaleString()} RECORDS ANALYZED
          </span>
          <h2 className="mt-3 text-xl font-semibold">Post-Sales AI Intelligence Pipeline</h2>
          <p className="mt-1 text-sm text-slate-200">
            Real-time Bayesian classification, symptom mapping, and failure root-cause detection.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="rounded-lg bg-white/10 px-5 py-3 text-center">
            <p className="text-xl font-bold">{pending ? `${pending} pending` : analyzed ? '100% Analyzed' : 'Awaiting data'}</p>
            <p className="text-[10px] uppercase tracking-wider text-slate-200">Pipeline Status</p>
          </div>
          {pending > 0 && (
            <button
              type="button"
              onClick={runAnalysis}
              disabled={running}
              className="rounded-lg bg-white px-4 py-2.5 text-sm font-semibold text-[#354E4B] hover:bg-slate-100 disabled:opacity-60"
            >
              {running ? 'Analyzing…' : `Analyze ${pending} pending`}
            </button>
          )}
        </div>
        {analysisMessage && <p role="status" className="w-full text-sm text-emerald-100 font-medium">{analysisMessage}</p>}
        {analysisError && <p role="alert" className="w-full text-sm text-rose-100 font-medium">{analysisError}</p>}
      </section>

      {/* SENTIMENT BREAKDOWN */}
      <section>
        <div className="mb-4">
          <p className="text-xs font-semibold uppercase text-[#52706A]">Sentiment Classification</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">Customer Sentiment Breakdown</h2>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          <MetricCard label="Positive" count={sentiment.positive} total={total} color="#6F4530" helper="Satisfied post-sales experience" />
          <MetricCard label="Neutral" count={sentiment.neutral} total={total} color="#C08A5B" helper="General operational inquiry" />
          <MetricCard label="Negative" count={sentiment.negative} total={total} color="#8B735E" helper="Reported failure, bug, or complaint" />
        </div>
      </section>

      {/* SEVERITY MATRIX */}
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase text-[#52706A]">Severity & Urgency</p>
        <h2 className="mt-1 text-lg font-semibold text-slate-900">Severity Prioritization Levels</h2>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { level: 'low', count: severity.low, desc: 'Minor cosmetic / inquiry', color: 'border-slate-200 bg-slate-50' },
            { level: 'medium', count: severity.medium, desc: 'Usability / minor bug', color: 'border-amber-200 bg-amber-50/50' },
            { level: 'high', count: severity.high, desc: 'Functional hardware failure', color: 'border-orange-200 bg-orange-50/60' },
            { level: 'critical', count: severity.critical, desc: 'Urgent hazard / outage', color: 'border-rose-200 bg-rose-50/70 text-rose-900' },
          ].map(({ level, count, desc, color }) => (
            <div key={level} className={`rounded-xl border p-4 ${color}`}>
              <div className="flex items-center justify-between">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-600">{level}</p>
                {level === 'critical' && <ShieldAlert className="h-4 w-4 text-rose-600" />}
              </div>
              <p className="mt-2 text-2xl font-bold text-slate-900">{Number(count || 0).toLocaleString()}</p>
              <p className="mt-1 text-xs text-slate-500">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* RANKED FAILURE CAUSES */}
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase text-[#52706A]">Objective 5 · Failure Prediction</p>
        <h2 className="mt-1 text-lg font-semibold text-slate-900">Ranked Technical Failure Causes</h2>
        <div className="mt-4 space-y-3">
          {causes.slice(0, 8).map((item, index) => {
            const pct = total ? ((item.count / total) * 100).toFixed(1) : 0;
            return (
              <div key={item.cause} className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-100 bg-slate-50/70 p-4">
                <div className="flex items-center gap-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#6F4530] text-xs font-bold text-white">
                    {index + 1}
                  </span>
                  <div>
                    <h3 className="font-semibold text-sm text-slate-900">{item.cause.replaceAll('_', ' ')}</h3>
                    <p className="text-xs text-slate-500">{pct}% of analyzed customer complaints</p>
                  </div>
                </div>
                <span className="shrink-0 rounded-full bg-white px-3 py-1 text-xs font-bold text-[#6F4530] shadow-sm">
                  {item.count} records
                </span>
              </div>
            );
          })}
          {!causes.length && <p className="py-8 text-center text-sm text-slate-500">No predicted causes available yet.</p>}
        </div>
      </section>

      {/* CLASSIFIED EVIDENCE TABLE */}
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Recent Customer Complaints & Symptoms</h2>
            <p className="text-xs text-slate-500">Linking customer-reported text to technical failure classifications</p>
          </div>
          <span className="text-xs text-slate-500">{feedback.length} records shown</span>
        </div>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[750px] text-left text-sm">
            <thead>
              <tr className="border-b text-xs uppercase tracking-wider text-slate-500">
                <th className="py-3 pr-3">Customer Feedback</th>
                <th className="px-3">Sentiment</th>
                <th className="px-3">Severity</th>
                <th className="py-3 px-3">Predicted Cause</th>
                <th className="py-3 pl-3">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {feedback.slice(0, 12).map((row, i) => (
                <tr key={row.id || i} className="hover:bg-slate-50/50">
                  <td className="max-w-md py-3 pr-3 text-xs leading-relaxed text-slate-800">
                    <p className="line-clamp-2">{row.feedback_text}</p>
                    {row.detected_symptoms?.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {row.detected_symptoms.map((s) => (
                          <span key={s} className="inline-flex items-center gap-0.5 rounded bg-amber-50 px-1.5 py-0.5 text-[10px] text-amber-800">
                            <Tags className="h-2.5 w-2.5" />
                            {s.replaceAll('_', ' ')}
                          </span>
                        ))}
                      </div>
                    )}
                  </td>
                  <td className="px-3">
                    <span className={`inline-block rounded-md px-2 py-0.5 text-xs font-semibold capitalize ${
                      row.sentiment === 'positive' ? 'bg-emerald-100 text-emerald-800' :
                      row.sentiment === 'negative' ? 'bg-rose-100 text-rose-800' :
                      'bg-slate-100 text-slate-700'
                    }`}>
                      {row.sentiment || 'neutral'}
                    </span>
                  </td>
                  <td className="px-3">
                    <span className={`inline-block rounded-md px-2 py-0.5 text-xs font-semibold uppercase ${
                      row.severity === 'critical' ? 'bg-rose-800 text-white' :
                      row.severity === 'high' ? 'bg-orange-600 text-white' :
                      'bg-slate-100 text-slate-700'
                    }`}>
                      {row.severity || 'low'}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-xs font-medium text-slate-800">
                    {row.predicted_cause || '—'}
                  </td>
                  <td className="py-3 pl-3 text-xs font-bold text-[#6F4530]">
                    {row.prediction_confidence ? `${row.prediction_confidence}%` : '—'}
                  </td>
                </tr>
              ))}
              {!feedback.length && (
                <tr>
                  <td colSpan="5" className="py-10 text-center text-slate-500">
                    No customer feedback records found. Upload a CSV or Excel file to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default Analysis;
