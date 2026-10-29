import { Info, TrendingUp } from 'lucide-react';

const colors = { positive: '#354E4B', neutral: '#A3B899', negative: '#C87557' };

function TrendsAnalysis({ data = {} }) {
  const total = Number(data.totalFeedback || 0);
  const sentiment = data.sentiment || {};
  const severity = data.severity || {};
  const daily = (data.daily || []).slice(-14);
  const maxDaily = Math.max(1, ...daily.map(day => day.positive + day.neutral + day.negative));
  const sentimentLabels = ['positive', 'neutral', 'negative'];
  const severityLabels = ['low', 'medium', 'high', 'critical'];

  return <div className="mx-auto max-w-7xl space-y-7 text-slate-800">
    <header><p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#52706A]">Trends</p><h1 className="mt-1 text-2xl font-bold text-slate-900 sm:text-3xl">Trends & analytics</h1><p className="mt-2 text-sm text-slate-600">Summaries and daily trends calculated from saved feedback records.</p></header>
    <div className="grid gap-5 xl:grid-cols-2">{[['Sentiment', sentimentLabels], ['Severity', severityLabels]].map(([title, labels]) => <section key={title} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">{title} distribution</h2><p className="mt-1 text-sm text-slate-500">{total.toLocaleString()} analyzed feedback records</p><div className="mt-5 space-y-4">{labels.map(label => { const count = Number((title === 'Sentiment' ? sentiment : severity)[label] || 0); const percent = total ? count / total * 100 : 0; const color = title === 'Sentiment' ? colors[label] : ({ low: '#354E4B', medium: '#A3B899', high: '#D99443', critical: '#C87557' })[label]; return <div key={label}><div className="mb-1 flex justify-between text-sm"><span className="capitalize">{label}</span><span className="font-semibold">{count.toLocaleString()} · {percent.toFixed(1)}%</span></div><div className="h-2.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full" style={{ width: `${percent}%`, backgroundColor: color }}/></div></div>; })}</div></section>)}</div>
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center gap-2"><TrendingUp className="h-5 w-5 text-[#52706A]"/><h2 className="text-lg font-semibold text-slate-900">Feedback activity by day</h2></div><p className="mt-1 text-sm text-slate-500">Daily sentiment counts based on record creation time.</p>{daily.length ? <div className="mt-5 space-y-4">{daily.map(day => { const sum = day.positive + day.neutral + day.negative; return <div key={day.date} className="grid grid-cols-[90px_1fr_45px] items-center gap-3"><span className="text-xs text-slate-500">{new Date(`${day.date}T00:00:00`).toLocaleDateString()}</span><div className="flex h-5 overflow-hidden rounded bg-slate-100" aria-label={`${sum} feedback on ${day.date}`}>{sentimentLabels.map(label => <span key={label} title={`${label}: ${day[label]}`} style={{ width: `${sum ? day[label] / maxDaily * 100 : 0}%`, backgroundColor: colors[label] }}/>)}</div><span className="text-right text-xs font-semibold text-slate-700">{sum}</span></div>; })}</div> : <div className="mt-5 rounded-lg border border-dashed border-slate-200 bg-slate-50 px-6 py-12 text-center"><Info className="mx-auto h-5 w-5 text-[#52706A]"/><p className="mt-2 text-sm font-medium text-slate-700">No daily trend data yet</p><p className="mt-1 text-xs text-slate-500">Upload and analyze a file to build this chart.</p></div>}</section>
  </div>;
}

export default TrendsAnalysis;
