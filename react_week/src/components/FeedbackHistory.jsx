import { useEffect, useState } from 'react';
import { apiRequest } from '../api';

const PAGE_SIZE = 25;
const exportUrl = `${(import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')}/api/feedback/export/`;

function FeedbackHistory({ reports = [] }) {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [records, setRecords] = useState([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const query = new URLSearchParams({ search, limit: String(PAGE_SIZE), offset: String(page * PAGE_SIZE) });
    apiRequest(`/api/feedback/?${query}`).then(data => {
      if (!active) return;
      setRecords(data.items);
      setTotal(data.total);
      setError('');
    }).catch(err => { if (active) setError(err.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [search, page]);

  const exportBatch = (filename) => `${exportUrl}?filename=${encodeURIComponent(filename)}`;
  return <div className="mx-auto max-w-7xl space-y-7">
    <header><p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#52706A]">Report library</p><h1 className="mt-1 text-2xl font-bold text-slate-900 sm:text-3xl">Feedback history</h1><p className="mt-2 text-sm text-slate-600">Search stored customer feedback and download the complete CSV archive.</p></header>
    <section className="flex flex-wrap items-center justify-between gap-5 rounded-xl border border-[#DCE7DE] bg-[#F7FAF7] p-6 shadow-sm"><div><p className="text-xs font-semibold uppercase tracking-wider text-[#52706A]">Stored feedback</p><h2 className="mt-1 text-lg font-semibold text-slate-900">{total.toLocaleString()} matching records</h2><p className="mt-1 text-sm text-slate-600">{reports.length} uploaded file{reports.length === 1 ? '' : 's'} in the archive.</p></div><a href={exportUrl} className="rounded-lg bg-[#354E4B] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#2C423F]">Download feedback CSV</a></section>
    <section className="space-y-5 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wider text-[#52706A]">Searchable records</p><h2 className="mt-1 text-lg font-semibold text-slate-900">All feedback</h2></div><label className="w-full max-w-sm text-xs font-medium text-slate-600">Search feedback text<input value={search} onChange={event => { setLoading(true); setSearch(event.target.value); setPage(0); }} placeholder="Search saved feedback…" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm" /></label></div>
      {error && <p role="alert" className="rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
      <div className="overflow-x-auto"><table className="w-full min-w-[850px] text-left text-sm"><thead><tr className="border-b text-xs uppercase text-slate-500"><th className="py-3 pr-3">Customer feedback</th><th className="px-3">File</th><th className="px-3">Sentiment</th><th className="px-3">Severity</th><th className="px-3">Predicted cause</th><th className="py-3 pl-3">Saved at</th></tr></thead><tbody className="divide-y divide-slate-100">{records.map(row => <tr key={row.id}><td className="max-w-xs truncate py-3 pr-3 text-slate-800">{row.feedback_text}</td><td className="max-w-[140px] truncate px-3 text-slate-600">{row.filename}</td><td className="px-3 capitalize">{row.sentiment}</td><td className="px-3 capitalize">{row.severity}</td><td className="px-3">{row.predicted_cause}</td><td className="py-3 pl-3 text-xs text-slate-500">{row.created_at ? new Date(row.created_at).toLocaleString() : '—'}</td></tr>)}{!loading && !records.length && <tr><td colSpan="6" className="py-12 text-center text-slate-500">{search ? 'No feedback matches this search.' : 'No feedback has been saved yet.'}</td></tr>}</tbody></table></div>
      {loading && <p className="text-sm text-slate-500">Loading feedback records…</p>}
      <div className="flex items-center justify-between border-t border-slate-100 pt-4"><p className="text-xs text-slate-500">Showing {total ? page * PAGE_SIZE + 1 : 0}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total.toLocaleString()}</p><div className="flex gap-2"><button type="button" onClick={() => { setLoading(true); setPage(value => Math.max(0, value - 1)); }} disabled={page === 0} className="rounded-lg border px-3 py-2 text-sm disabled:opacity-40">Previous</button><button type="button" onClick={() => { setLoading(true); setPage(value => value + 1); }} disabled={(page + 1) * PAGE_SIZE >= total} className="rounded-lg border px-3 py-2 text-sm disabled:opacity-40">Next</button></div></div>
    </section>
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">Uploaded file reports</h2><div className="mt-4 divide-y divide-slate-100">{reports.map(report => <div key={report.filename} className="flex flex-wrap items-center justify-between gap-3 py-3"><div><p className="font-medium text-slate-800">{report.filename}</p><p className="text-xs text-slate-500">{report.feedback_count.toLocaleString()} records · {report.created_at ? new Date(report.created_at).toLocaleString() : ''} · {report.critical} critical</p></div><a href={exportBatch(report.filename)} className="text-sm font-semibold text-[#354E4B] underline">Download file records</a></div>)}{!reports.length && <p className="py-6 text-sm text-slate-500">No uploaded reports yet.</p>}</div></section>
  </div>;
}

export default FeedbackHistory;
