import { useMemo, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  ChartColumnIncreasing,
  CircleCheck,
  CloudUpload,
  FileText,
  MessageSquareText,
  Search,
  ShieldCheck,
  Smile,
  Tags,
  Upload,
  Users,
  X,
  Zap,
} from 'lucide-react';
import { uploadFeedbackFile } from '../api';
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Legend, Tooltip);

function formatRelativeTime(value) {
  if (!value) return '';
  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) return '';
  const minutes = Math.max(1, Math.floor((Date.now() - timestamp) / 60000));
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return days < 7 ? `${days}d ago` : new Date(value).toLocaleDateString();
}

function createIdempotencyKey() {
  return globalThis.crypto?.randomUUID?.()
    || `upload-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function DashCards({
  onUploadComplete,
  feedback = [],
  feedbackTotal = 0,
  dailyTrends = [],
  summary = {},
  latestBatch = null,
  onNavigate,
}) {
  const [selectedFileType, setSelectedFileType] = useState('csv');
  const [selectedFile, setSelectedFile] = useState(null);
  const [idempotencyKey, setIdempotencyKey] = useState(createIdempotencyKey);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  // Compute live metrics from summary
  const sentiment = summary.sentiment || {};
  const severity = summary.severity || {};
  const causes = summary.causes || [];
  const topCause = causes[0]?.cause || 'Awaiting Analysis';
  const highPriorityCount = (severity.high || 0) + (severity.critical || 0);
  // Count of the most recent upload batch only (not the whole database)
  const latestBatchCount = Number(latestBatch?.feedback_count || 0);

  const preview = useMemo(() => {
    if (result?.records && result.records.length > 0) return result.records;
    return feedback;
  }, [result, feedback]);

  const BAR_COLORS = dailyTrends.map((_, i) => {
    const palette = ['#6F4530', '#C08A5B', '#52706A', '#9B6A45', '#3B5E58', '#A07548', '#7A4F30', '#5E8079'];
    return palette[i % palette.length];
  });

  const volumeChart = {
    labels: dailyTrends.map((item) => item.date),
    datasets: [{
      label: 'Feedback count',
      data: dailyTrends.map((item) => item.feedback_count),
      backgroundColor: BAR_COLORS,
      hoverBackgroundColor: BAR_COLORS.map(() => '#3B1F12'),
      borderRadius: 7,
      borderSkipped: false,
      maxBarThickness: 44,
    }],
  };

  const volumeChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#3B1F12',
        titleColor: '#F3E6D7',
        bodyColor: '#E8D1B5',
        titleFont: { size: 12, weight: 'bold' },
        bodyFont: { size: 12 },
        padding: 12,
        displayColors: false,
        callbacks: {
          title: (ctx) => `📅 ${ctx[0].label}`,
          label: (ctx) => `  ${ctx.parsed.y} feedback records`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        title: { display: true, text: 'Date', color: '#6F4530', font: { weight: 'bold', size: 11 } },
        ticks: { color: '#64748B', font: { size: 10 } },
      },
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(0,0,0,0.05)' },
        ticks: { precision: 0, color: '#64748B', font: { size: 10 } },
        title: { display: true, text: 'Feedback Count', color: '#6F4530', font: { weight: 'bold', size: 11 } },
      },
    },
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    if (selectedFileType === 'pdf') {
      setError('PDF uploads are not supported. Choose a CSV or XLSX file.');
      return;
    }
    const expectedExtension = selectedFileType === 'csv' ? '.csv' : '.xlsx';
    if (!selectedFile.name.toLowerCase().endsWith(expectedExtension)) {
      setError(`Choose a ${expectedExtension.toUpperCase()} file to upload feedback.`);
      return;
    }
    setUploading(true);
    setError('');
    setResult(null);
    try {
      const payload = await uploadFeedbackFile(selectedFile, idempotencyKey);
      setResult(payload);
      if (onUploadComplete) {
        await onUploadComplete(payload);
      }
    } catch (uploadError) {
      setError(uploadError.message || 'Upload failed. Check that the FastAPI backend is running on http://127.0.0.1:8000.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="dashboard-home mx-auto w-full max-w-7xl space-y-6">
      {/* WELCOME BANNER */}
      <section className="dashboard-welcome-banner relative isolate overflow-hidden rounded-2xl px-5 py-3 shadow-lg sm:px-7 sm:py-3 lg:px-8" aria-labelledby="dashboard-welcome-title">
        <div className="dashboard-welcome-banner__glow" aria-hidden="true" />
        <div className="relative z-10 grid min-h-32 items-center gap-2 sm:min-h-36 lg:grid-cols-2 lg:gap-4">
          <div className="max-w-2xl">
            <p className="mb-2 inline-flex items-center gap-2 text-[11px] font-semibold tracking-[0.16em] text-[#E8D1B5] sm:text-xs">
              <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#C08A5B]/20 text-[#D9A36A]"><BrainCircuit className="h-3.5 w-3.5" /></span>
              AI-BASED POST-SALES FEEDBACK INTELLIGENCE
            </p>
            <h1 id="dashboard-welcome-title" className="max-w-xl text-2xl font-bold leading-tight tracking-tight text-[#FFFDF9] sm:text-3xl lg:text-[2.1rem]">
              Post-Sales Analysis & <span className="text-[#D9A36A]">Failure Prediction</span>
            </h1>
            <p className="mt-2 max-w-md text-sm leading-5 text-[#F3E6D7] sm:text-[15px]">
              Classify unstructured customer complaints, extract failure symptoms, rank root causes, and generate early warnings.
            </p>
            <ul className="mt-5 flex flex-wrap gap-x-4 gap-y-2.5 text-[11px] font-medium text-[#FFFDF9] sm:gap-x-5 sm:text-xs">
              <li className="inline-flex items-center gap-2"><Users className="h-3.5 w-3.5 text-[#D9A36A]" />NLP Sentiment & Severity</li>
              <li className="inline-flex items-center gap-2"><Search className="h-3.5 w-3.5 text-[#D9A36A]" />Symptom-to-Failure Mapping</li>
              <li className="inline-flex items-center gap-2"><ShieldCheck className="h-3.5 w-3.5 text-[#D9A36A]" />Early Warning Detection</li>
            </ul>
          </div>

          <div className="relative mx-auto mt-1 aspect-[3.07/1] w-full max-w-[27rem] sm:mt-0">
            <img
              src="/ai-postsale-welcome.png"
              alt="AI analyzing customer feedback and predicting failure patterns"
              className="h-full w-full object-cover"
            />
          </div>
        </div>
      </section>

      {/* DYNAMIC METRIC SUMMARY CARDS */}
      <section aria-label="Dashboard summary" className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {/* Card 1: Sentiment Analysis */}
        <article
          onClick={() => onNavigate?.('Trends Analysis')}
          className="dashboard-summary-card flex min-h-28 cursor-pointer items-start gap-3 rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm transition-all hover:border-[#C08A5B] hover:shadow-md sm:p-4"
        >
          <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#C08A5B] text-white">
            <Smile className="h-5 w-5" />
          </span>
          <div className="flex min-w-0 flex-1 flex-col self-stretch">
            <h2 className="text-xs font-semibold text-slate-900 sm:text-sm">Sentiment Analysis</h2>
            <p className="mt-1 text-sm font-bold text-slate-800">
              {sentiment.positive ? `${sentiment.positive} Pos · ${sentiment.negative} Neg` : 'Awaiting data'}
            </p>
            <p className="mt-1 text-[11px] text-slate-500">
              {sentiment.neutral ? `${sentiment.neutral} neutral feedback` : 'Customer sentiment breakdown'}
            </p>
            <span className="mt-auto ml-auto inline-flex items-center gap-1 text-[11px] font-semibold text-[#8B4F2C]">
              View Trends <ArrowRight className="h-3.5 w-3.5" />
            </span>
          </div>
        </article>

        {/* Card 2: Severity Analysis */}
        <article
          onClick={() => onNavigate?.('Early Warnings')}
          className="dashboard-summary-card flex min-h-28 cursor-pointer items-start gap-3 rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm transition-all hover:border-[#C08A5B] hover:shadow-md sm:p-4"
        >
          <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-rose-600 text-white">
            <AlertTriangle className="h-5 w-5" />
          </span>
          <div className="flex min-w-0 flex-1 flex-col self-stretch">
            <h2 className="text-xs font-semibold text-slate-900 sm:text-sm">Severity & Early Warnings</h2>
            <p className="mt-1 text-sm font-bold text-rose-700">
              {highPriorityCount > 0 ? `${highPriorityCount} High / Critical` : '0 Critical Issues'}
            </p>
            <p className="mt-1 text-[11px] text-slate-500">
              {severity.critical ? `${severity.critical} safety/urgent alerts` : 'Prioritized failure risks'}
            </p>
            <span className="mt-auto ml-auto inline-flex items-center gap-1 text-[11px] font-semibold text-[#8B4F2C]">
              View Alerts <ArrowRight className="h-3.5 w-3.5" />
            </span>
          </div>
        </article>

        {/* Card 3: Failure Prediction */}
        <article
          onClick={() => onNavigate?.('AI Insights')}
          className="dashboard-summary-card flex min-h-28 cursor-pointer items-start gap-3 rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm transition-all hover:border-[#C08A5B] hover:shadow-md sm:p-4"
        >
          <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#354E4B] text-white">
            <BrainCircuit className="h-5 w-5" />
          </span>
          <div className="flex min-w-0 flex-1 flex-col self-stretch">
            <h2 className="text-xs font-semibold text-slate-900 sm:text-sm">Failure Prediction</h2>
            <p className="mt-1 truncate text-xs font-bold text-slate-800" title={topCause}>
              {topCause}
            </p>
            <p className="mt-1 text-[11px] text-slate-500">
              {causes.length > 0 ? `${causes.length} recurring failure patterns` : 'Predictive root-cause ranking'}
            </p>
            <span className="mt-auto ml-auto inline-flex items-center gap-1 text-[11px] font-semibold text-[#8B4F2C]">
              View AI Insights <ArrowRight className="h-3.5 w-3.5" />
            </span>
          </div>
        </article>

        {/* Card 4: Uploaded Feedback (this upload only — not the whole database) */}
        <article className="dashboard-summary-card dashboard-summary-card--featured flex min-h-28 items-start gap-3 rounded-xl border border-slate-200 bg-[#F3E6D7] p-3.5 shadow-sm sm:p-4">
          <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#6F4530] text-white">
            <FileText className="h-5 w-5" />
          </span>
          <div className="flex min-w-0 flex-1 flex-col self-stretch">
            <h2 className="text-xs font-semibold text-slate-900 sm:text-sm">Uploaded Feedback</h2>
            <p className="mt-1 text-xl font-bold leading-tight text-slate-900 sm:text-2xl">
              {(result?.new_records_uploaded ?? latestBatchCount).toLocaleString()} records
            </p>
            {(result?.new_records_uploaded ?? latestBatchCount) > 0 && (
              <span className="mt-2 inline-flex w-fit items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-800">
                <CircleCheck className="h-3 w-3" /> {result ? 'Uploaded this session' : 'Latest upload batch'}
              </span>
            )}
          </div>
        </article>
      </section>

      {/* MAIN TWO-COLUMN DASHBOARD CONTENT */}
      <div className="grid grid-cols-1 items-stretch gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(20rem,1fr)]">
        <div className="space-y-4">
          {/* UPLOAD FORM SECTION */}
          <section className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm sm:p-4">
            <div className="mb-3 flex items-center gap-3">
              <CloudUpload className="h-6 w-6 shrink-0 text-[#6F4530]" />
              <div>
                <h2 className="text-base font-semibold text-slate-900">Upload Feedback & Service Records</h2>
                <p className="text-[11px] text-slate-600">
                  Ingest customer complaints, warranty reports, and return forms (CSV or Excel).
                </p>
              </div>
            </div>

            <label className="mb-2 block text-xs font-medium text-slate-700">
              File type
              <select
                value={selectedFileType}
                onChange={(event) => {
                  setSelectedFileType(event.target.value);
                  setSelectedFile(null);
                  setIdempotencyKey(createIdempotencyKey());
                  setError('');
                  setResult(null);
                }}
                className="mt-1 block w-full rounded-lg border border-[#E5D6C7] bg-[#FFFDF9] px-3 py-1.5 text-sm text-slate-800 focus:border-[#C08A5B] focus:outline-none"
              >
                <option value="csv">CSV (.csv)</option>
                <option value="excel">Excel (.xlsx)</option>
                <option value="pdf">PDF (.pdf - not supported)</option>
              </select>
            </label>

            <label className="relative flex min-h-12 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-[#E5D6C7] bg-[#F8F3ED] px-4 py-1 text-center transition-colors hover:bg-[#F3E6D7] sm:min-h-14">
              {selectedFile ? <FileText className="mb-2 h-7 w-7 text-[#6F4530]" /> : <Upload className="mb-2 h-8 w-8 text-[#6F4530]" />}
              <span className="max-w-full truncate text-sm font-semibold text-slate-800">
                {selectedFile?.name || `Choose a ${selectedFileType === 'excel' ? 'Excel (.xlsx)' : 'CSV (.csv)'} file to upload`}
              </span>
              <span className="mt-1 text-xs text-slate-500">
                {selectedFile ? 'Click to choose another file' : selectedFileType === 'pdf' ? 'PDF upload is not supported' : `${selectedFileType === 'csv' ? 'CSV' : 'XLSX'} file · up to 25 MiB`}
              </span>
              {selectedFile && <X aria-hidden="true" className="absolute right-4 top-4 h-4 w-4 text-[#6F4530]" />}
              <input
                type="file"
                accept={selectedFileType === 'csv' ? '.csv,text/csv' : selectedFileType === 'pdf' ? '.pdf,application/pdf' : '.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}
                className="sr-only"
                onChange={(event) => {
                  const file = event.target.files?.[0] || null;
                  setSelectedFile(file);
                  setIdempotencyKey(createIdempotencyKey());
                  event.target.value = '';
                  setError('');
                  setResult(null);
                }}
              />
            </label>

            <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-slate-600">
                Uploaded at this time: <strong className="text-slate-900">{(result?.new_records_uploaded ?? latestBatchCount).toLocaleString()}</strong>
              </p>
              <button
                type="button"
                onClick={handleUpload}
                disabled={!selectedFile || uploading || selectedFileType === 'pdf'}
                className="inline-flex items-center gap-2 rounded-lg bg-[#6F4530] px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#593722] disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {uploading ? (
                  <>
                    <Zap className="h-4 w-4 animate-spin" /> Ingesting & Analyzing…
                  </>
                ) : selectedFileType === 'pdf' ? (
                  'Format not supported'
                ) : selectedFile ? (
                  'Upload feedback'
                ) : (
                  'Choose a file first'
                )}
              </button>
            </div>

            {selectedFileType === 'pdf' && (
              <p className="mt-3 rounded-lg bg-[#F3E6D7] p-3 text-xs leading-5 text-[#6F4530]">
                PDF files are not supported. Upload customer feedback records as CSV or Excel.
              </p>
            )}

            {error && (
              <div role="alert" className="mt-3 rounded-lg bg-rose-50 p-3.5 text-sm text-rose-800">
                <p className="font-semibold">Upload Error:</p>
                <p className="mt-0.5 text-xs">{error}</p>
              </div>
            )}

            {result && (
              <div role="status" className="mt-3 rounded-lg bg-emerald-50 p-3.5 text-xs text-emerald-900 space-y-1">
                <p className="font-bold text-sm text-emerald-950">{result.message}</p>
                <p>
                  <strong>{result.new_records_uploaded}</strong> records uploaded & analyzed at this time · <strong>{result.duplicate_records_skipped}</strong> duplicates skipped · <strong>{result.invalid_rows_skipped}</strong> invalid rows skipped.
                </p>
              </div>
            )}
          </section>

          {/* DATE TREND GRAPH SECTION */}
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <ChartColumnIncreasing className="h-5 w-5 text-[#6F4530]" />
                <h2 className="text-lg font-semibold text-slate-900">Feedback Volume Timeline</h2>
              </div>
              <span className="text-xs text-slate-500">Service / complaint dates</span>
            </div>
            {dailyTrends.length ? (
              <>
                <div className="h-64" role="img" aria-label="Feedback count histogram by service or feedback date">
                  <Bar data={volumeChart} options={volumeChartOptions} />
                </div>
                <p className="mt-3 rounded-lg bg-[#F8F3ED] px-4 py-2.5 text-xs leading-5 text-[#6F4530]">
                  📊 <strong>How to read this chart:</strong> Each bar represents one day's total feedback volume.
                  Taller bars mean more customer complaints or service records were received that day —
                  a quick visual signal for quality teams to prioritize investigations.
                </p>
              </>
            ) : (
              <div className="flex h-64 flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50 px-4 text-center">
                <p className="text-sm font-medium text-slate-700">No dated feedback to chart yet</p>
                <p className="mt-1 text-xs text-slate-500">
                  Upload a feedback file containing service dates or complaint timestamps to display the failure trend timeline.
                </p>
              </div>
            )}
          </section>
        </div>

        {/* RECENT UPLOADED FEEDBACKS WITH CLASSIFICATION TAGS */}
        <section className="flex min-h-[30rem] min-w-0 flex-col overflow-hidden rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5 xl:h-full xl:max-h-[50rem]">
          <div className="mb-2 flex items-center justify-between gap-3 border-b border-slate-100 pb-3">
            <div className="flex min-w-0 items-center gap-2.5">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#F3E6D7] text-[#6F4530]">
                <MessageSquareText className="h-4 w-4" />
              </span>
              <div>
                <h2 className="truncate text-sm font-semibold text-slate-900 sm:text-base">Classified Customer Feedback</h2>
                <p className="text-[11px] text-slate-500">NLP sentiment, symptoms & failure cause</p>
              </div>
            </div>
            <span className="shrink-0 text-[11px] text-slate-500">
              <strong className="text-slate-800">{feedbackTotal.toLocaleString()}</strong> records
            </span>
          </div>

          <div className="min-h-0 flex-1 divide-y divide-slate-100 overflow-y-auto pr-1">
            {preview.slice(0, 15).map((row, index) => {
              const isPos = row.sentiment === 'positive';
              const isNeg = row.sentiment === 'negative';
              const isCrit = row.severity === 'critical';
              const isHigh = row.severity === 'high';

              return (
                <article key={row.id || `${row.feedback_text}-${index}`} className="py-3 first:pt-1">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs leading-relaxed text-slate-800 font-medium">{row.feedback_text}</p>
                    <time className="shrink-0 text-[10px] text-slate-400">{formatRelativeTime(row.created_at)}</time>
                  </div>

                  {/* AI CLASSIFICATION TAGS */}
                  <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[10px]">
                    {/* Sentiment Tag */}
                    <span className={`rounded-md px-2 py-0.5 font-semibold capitalize ${
                      isPos ? 'bg-emerald-100 text-emerald-800' : isNeg ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {row.sentiment || 'neutral'}
                    </span>

                    {/* Severity Tag */}
                    <span className={`rounded-md px-2 py-0.5 font-semibold uppercase ${
                      isCrit ? 'bg-rose-800 text-white' : isHigh ? 'bg-orange-600 text-white' : 'bg-slate-100 text-slate-700'
                    }`}>
                      {row.severity || 'low'}
                    </span>

                    {/* Predicted Failure Cause */}
                    {row.predicted_cause && (
                      <span className="rounded-md bg-[#F1F6F1] px-2 py-0.5 font-medium text-[#354E4B]" title="Predicted Root Cause">
                        Cause: {row.predicted_cause.replaceAll('_', ' ')}
                      </span>
                    )}

                    {/* Prediction Confidence */}
                    {row.prediction_confidence > 0 && (
                      <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-slate-600 font-bold">
                        {row.prediction_confidence}% conf
                      </span>
                    )}

                    {/* Detected Symptoms */}
                    {Array.isArray(row.detected_symptoms) && row.detected_symptoms.map((sym) => (
                      <span key={sym} className="inline-flex items-center gap-1 rounded-md bg-amber-50 px-1.5 py-0.5 text-amber-900">
                        <Tags className="h-2.5 w-2.5 text-amber-700" />
                        {sym.replaceAll('_', ' ')}
                      </span>
                    ))}
                  </div>
                </article>
              );
            })}

            {!preview.length && (
              <div className="py-16 text-center">
                <FileText className="mx-auto h-8 w-8 text-slate-300" />
                <p className="mt-2 text-sm font-medium text-slate-600">No customer feedback loaded yet</p>
                <p className="mt-1 text-xs text-slate-400">Upload a CSV or Excel file above to see classified records here.</p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

export default DashCards;
