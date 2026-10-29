import { useMemo, useState } from 'react';
import { AlertTriangle, FileText, Search, Smile, TrendingUp, Upload } from 'lucide-react';
import { uploadFeedbackFile } from '../api';

function DashCards({ onNavigateToAnalyze, onUploadComplete, feedback = [], feedbackTotal = 0, summary = {} }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const preview = useMemo(() => result?.records || feedback, [result, feedback]);
  const sentiments = summary.sentiment || {};
  const negative = Number(sentiments.negative || 0);

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setError('');
    setResult(null);
    try {
      const payload = await uploadFeedbackFile(selectedFile);
      setResult(payload);
      await onUploadComplete?.(payload);
    } catch (uploadError) {
      setError(uploadError.message || 'Upload failed. Check that the API and database are running.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="dashboard-home mx-auto w-full max-w-7xl space-y-7">
      <header className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#52706A]">Dashboard overview</p>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Customer intelligence</h1>
        <p className="max-w-2xl text-sm leading-6 text-slate-600">Upload a CSV to analyze and save every feedback record for the dashboard and reports.</p>
      </header>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { label: 'Saved feedback', value: feedbackTotal, icon: FileText },
          { label: 'Positive feedback', value: sentiments.positive || 0, icon: Smile },
          { label: 'Negative feedback', value: negative, icon: AlertTriangle },
          { label: 'Predicted causes', value: summary.causes?.length || 0, icon: Search },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#E8EFEA] text-[#354E4B]"><Icon className="h-5 w-5" /></span>
            <div><p className="text-xs text-slate-500">{label}</p><p className="text-2xl font-bold text-slate-900">{Number(value).toLocaleString()}</p></div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div><p className="text-xs font-semibold uppercase tracking-wider text-[#52706A]">Import data</p><h2 className="mt-1 text-lg font-semibold text-slate-900">Upload feedback CSV</h2><p className="mt-1 text-sm text-slate-500">Choose a CSV with a feedback_text, feedback, text, comment, review, or message column.</p></div>
          <label className="flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-[#A3B899] bg-[#F7FAF7] p-5 text-center hover:bg-[#F1F6F1]">
            <Upload className="mb-2 h-6 w-6 text-[#354E4B]" />
            <span className="text-sm font-semibold text-slate-800">Choose CSV file</span>
            <span className="mt-1 max-w-full truncate text-xs text-slate-500">{selectedFile?.name || 'CSV up to 20 MiB'}</span>
            <input type="file" accept=".csv,text/csv" className="sr-only" onChange={(event) => { setSelectedFile(event.target.files?.[0] || null); setError(''); setResult(null); }} />
          </label>
          <button type="button" onClick={handleUpload} disabled={!selectedFile || uploading} className="w-full rounded-lg bg-[#354E4B] px-4 py-3 text-sm font-semibold text-white hover:bg-[#2C423F] disabled:cursor-not-allowed disabled:bg-slate-300">
            {uploading ? 'Analyzing and saving…' : 'Analyze and save feedback'}
          </button>
          {error && <p role="alert" className="rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
          {result && <div role="status" className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-900"><strong>{result.saved_rows} records saved.</strong> {result.analyzed_rows} analyzed from {result.filename}.</div>}
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm xl:col-span-2">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <div><p className="text-xs font-semibold uppercase tracking-wider text-[#52706A]">Stored records</p><h2 className="mt-1 text-lg font-semibold text-slate-900">Recent feedback</h2></div>
            <span className="rounded-full bg-[#E8EFEA] px-3 py-1.5 text-xs font-semibold text-[#354E4B]">{feedbackTotal.toLocaleString()} total</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[620px] text-left text-sm">
              <thead><tr className="border-b border-slate-200 text-xs uppercase text-slate-500"><th className="py-3 pr-3">Feedback</th><th className="py-3 px-3">Sentiment</th><th className="py-3 px-3">Severity</th><th className="py-3 pl-3">Predicted cause</th></tr></thead>
              <tbody className="divide-y divide-slate-100">
                {preview.slice(0, 8).map((row, index) => <tr key={row.id || `${row.feedback_text}-${index}`}><td className="max-w-sm truncate py-3 pr-3 text-slate-700">{row.feedback_text}</td><td className="px-3 py-3 capitalize">{row.sentiment}</td><td className="px-3 py-3 capitalize">{row.severity}</td><td className="py-3 pl-3 text-slate-600">{row.predicted_cause}</td></tr>)}
                {!preview.length && <tr><td colSpan="4" className="py-12 text-center text-sm text-slate-500">No feedback has been saved yet. Upload a CSV to get started.</td></tr>}
              </tbody>
            </table>
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
            <p className="text-xs text-slate-500">Showing {Math.min(8, preview.length)} recent records of {feedbackTotal.toLocaleString()} saved.</p>
            <button type="button" onClick={onNavigateToAnalyze} className="inline-flex items-center gap-2 rounded-lg bg-[#354E4B] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#2C423F]"><TrendingUp className="h-4 w-4" /> Open analysis</button>
          </div>
        </section>
      </div>
    </div>
  );
}

export default DashCards;
