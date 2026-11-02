import { useState } from 'react';
import { apiFetch } from '../api';

function ReportDownloads({ reports = [], totalFeedback = 0 }) {
  const [downloading, setDownloading] = useState('');
  const [downloadError, setDownloadError] = useState('');

  const download = async (path, label) => {
    setDownloading(label);
    setDownloadError('');
    try {
      const response = await apiFetch(path);
      const blob = await response.blob();
      const disposition = response.headers.get('content-disposition') || '';
      const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || label;
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = objectUrl;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    } catch (error) {
      setDownloadError(error.message || 'Report download failed. Check the backend connection and try again.');
    } finally {
      setDownloading('');
    }
  };

  const batchPath = (path, batchId) => `${path}?batch_id=${encodeURIComponent(batchId)}`;

  return <div className="mx-auto max-w-7xl space-y-7">
    <header>
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#52706A]">Report library</p>
      <h1 className="mt-1 text-2xl font-bold text-slate-900 sm:text-3xl">Feedback history</h1>
      <p className="mt-2 text-sm text-slate-600">Download complete feedback reports for safe keeping and future reference.</p>
    </header>

    <section className="flex flex-wrap items-center justify-between gap-5 rounded-xl border border-[#DCE7DE] bg-[#F7FAF7] p-6 shadow-sm">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-[#52706A]">Stored records</p>
        <h2 className="mt-1 text-lg font-semibold text-slate-900">{totalFeedback.toLocaleString()} feedback records</h2>
        <p className="mt-1 text-sm text-slate-600">Reports include all records and their current analysis status.</p>
      </div>
      <div className="flex flex-wrap gap-3">
        <button type="button" onClick={() => download('/api/reports/analysis-report.pdf', 'analysis-report.pdf')} disabled={Boolean(downloading)} className="rounded-lg bg-[#6F4530] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#563722] disabled:opacity-60">{downloading === 'analysis-report.pdf' ? 'Preparing PDF…' : 'Download PDF analysis report'}</button>
        <button type="button" onClick={() => download('/api/reports/feedback.csv', 'feedback-report.csv')} disabled={Boolean(downloading)} className="rounded-lg bg-[#354E4B] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#2C423F] disabled:opacity-60">{downloading === 'feedback-report.csv' ? 'Preparing CSV…' : 'Download CSV report'}</button>
        <button type="button" onClick={() => download('/api/reports/feedback.xlsx', 'feedback-report.xlsx')} disabled={Boolean(downloading)} className="rounded-lg border border-[#354E4B] px-4 py-2.5 text-sm font-semibold text-[#354E4B] hover:bg-white disabled:opacity-60">{downloading === 'feedback-report.xlsx' ? 'Preparing Excel…' : 'Download Excel report'}</button>
      </div>
      {downloadError && <p role="alert" className="w-full text-sm text-rose-800">{downloadError}</p>}
    </section>

    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-[#52706A]">Upload batches</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">Download a batch report</h2>
        </div>
        <span className="text-sm text-slate-500">{reports.length} upload batches</span>
      </div>
      <div className="mt-4 divide-y divide-slate-100">
        {reports.map((report) => (
          <div key={report.id} className="flex flex-wrap items-center justify-between gap-3 py-4">
            <div>
              <p className="font-medium text-slate-800">{report.filename}</p>
              <p className="text-xs text-slate-500">
                {Number(report.feedback_count || 0).toLocaleString()} new records · {report.created_at ? new Date(report.created_at).toLocaleString() : 'Upload time unavailable'}
                {report.duplicate_records_skipped ? ` · ${report.duplicate_records_skipped} duplicates skipped` : ''}
              </p>
            </div>
            <div className="flex gap-3 text-sm font-semibold text-[#354E4B]">
              <button type="button" disabled={Boolean(downloading)} onClick={() => download(batchPath('/api/reports/feedback.csv', report.id), `feedback-batch-${report.id}.csv`)} className="underline disabled:opacity-50">CSV</button>
              <button type="button" disabled={Boolean(downloading)} onClick={() => download(batchPath('/api/reports/feedback.xlsx', report.id), `feedback-batch-${report.id}.xlsx`)} className="underline disabled:opacity-50">Excel</button>
              <button type="button" disabled={Boolean(downloading)} onClick={() => download(batchPath('/api/reports/analysis-report.pdf', report.id), `analysis-report-${report.id}.pdf`)} className="underline disabled:opacity-50">PDF</button>
            </div>
          </div>
        ))}
        {!reports.length && <p className="py-8 text-center text-sm text-slate-500">No upload batches are available yet.</p>}
      </div>
    </section>
  </div>;
}

export default ReportDownloads;
