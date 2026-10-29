const MetricCard = ({ label, count, total, color, helper }) => {
  const percent = total ? Math.round((count / total) * 100) : 0;
  return <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
    <div className="flex justify-between text-sm font-semibold text-slate-800"><span>{label}</span><span>{percent}%</span></div>
    <p className="text-3xl font-bold text-slate-900">{Number(count || 0).toLocaleString()}</p>
    <div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full" style={{ width: `${percent}%`, backgroundColor: color }} /></div>
    <p className="text-xs text-slate-500">{helper}</p>
  </div>;
};

function Analysis({ summary = {}, feedback = [] }) {
  const total = Number(summary.total_feedback || 0);
  const sentiment = summary.sentiment || {};
  const severity = summary.severity || {};
  const causes = summary.causes || [];
  return <div className="mx-auto max-w-7xl space-y-7">
    <header><p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#52706A]">Analyze</p><h1 className="mt-1 text-2xl font-bold text-slate-900 sm:text-3xl">Customer intelligence</h1><p className="mt-2 text-sm text-slate-600">Analysis from feedback records saved in PostgreSQL.</p></header>
    <section className="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-[#354E4B] p-6 text-white"><div><span className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold">{total.toLocaleString()} RECORDS ANALYZED</span><h2 className="mt-3 text-xl font-semibold">Feedback analysis summary</h2><p className="mt-1 text-sm text-slate-200">Sentiment, severity, and predicted root causes across uploaded files.</p></div><div className="rounded-lg bg-white/10 px-5 py-3 text-center"><p className="text-xl font-bold">{total ? 'Complete' : 'Awaiting data'}</p><p className="text-[10px] uppercase tracking-wider text-slate-200">Analysis status</p></div></section>
    <section><div className="mb-4"><p className="text-xs font-semibold uppercase text-[#52706A]">Sentiment</p><h2 className="mt-1 text-lg font-semibold text-slate-900">Customer sentiment breakdown</h2></div><div className="grid gap-5 md:grid-cols-3"><MetricCard label="Positive" count={sentiment.positive} total={total} color="#354E4B" helper="Classified as positive"/><MetricCard label="Neutral" count={sentiment.neutral} total={total} color="#A3B899" helper="Classified as neutral"/><MetricCard label="Negative" count={sentiment.negative} total={total} color="#C87557" helper="Classified as negative"/></div></section>
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-xs font-semibold uppercase text-[#52706A]">Severity</p><h2 className="mt-1 text-lg font-semibold text-slate-900">Severity levels</h2><div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{['low', 'medium', 'high', 'critical'].map(level => <div key={level} className="rounded-lg bg-slate-50 p-4"><p className="text-sm capitalize text-slate-600">{level}</p><p className="mt-1 text-2xl font-bold text-slate-900">{Number(severity[level] || 0).toLocaleString()}</p></div>)}</div></section>
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-xs font-semibold uppercase text-[#52706A]">Failure analysis</p><h2 className="mt-1 text-lg font-semibold text-slate-900">Most common predicted causes</h2><div className="mt-4 space-y-3">{causes.slice(0, 8).map(item => <div key={item.cause} className="flex items-center justify-between gap-4 rounded-lg bg-slate-50 px-4 py-3"><span className="text-sm text-slate-700">{item.cause.replaceAll('_', ' ')}</span><span className="shrink-0 rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700">{item.count} records</span></div>)}{!causes.length && <p className="py-8 text-center text-sm text-slate-500">No predicted causes available yet.</p>}</div></section>
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">Recent analyzed feedback</h2><div className="mt-4 overflow-x-auto"><table className="w-full min-w-[650px] text-left text-sm"><thead><tr className="border-b text-xs uppercase text-slate-500"><th className="py-3 pr-3">Feedback</th><th className="px-3">Sentiment</th><th className="px-3">Severity</th><th className="py-3 pl-3">Predicted cause</th></tr></thead><tbody className="divide-y">{feedback.slice(0, 10).map((row, i) => <tr key={row.id || i}><td className="max-w-md truncate py-3 pr-3">{row.feedback_text}</td><td className="px-3 capitalize">{row.sentiment}</td><td className="px-3 capitalize">{row.severity}</td><td className="py-3 pl-3">{row.predicted_cause}</td></tr>)}{!feedback.length && <tr><td colSpan="4" className="py-8 text-center text-slate-500">No saved records found.</td></tr>}</tbody></table></div></section>
  </div>;
}

export default Analysis;
