import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { BarChart3, HelpCircle, Info, Sparkles, TrendingUp } from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const colors = { positive: '#52706A', neutral: '#C08A5B', negative: '#8B4F2C' };

function TrendsAnalysis({ data = {} }) {
  const total = Number(data.totalFeedback || 0);
  const sentiment = data.sentiment || {};
  const severity = data.severity || {};
  const daily = (data.daily || []).slice(-14);

  const sentimentLabels = ['positive', 'neutral', 'negative'];
  const severityLabels = ['low', 'medium', 'high', 'critical'];

  // Histogram Chart Configuration (Stacked Daily Sentiment Distribution)
  const histogramData = {
    labels: daily.map((d) => {
      try {
        const parts = d.date.split('-');
        if (parts.length === 3) return `${parts[1]}/${parts[2]}`;
        return d.date;
      } catch {
        return d.date;
      }
    }),
    datasets: [
      {
        label: 'Negative Complaints',
        data: daily.map((d) => d.negative || 0),
        backgroundColor: '#8B4F2C',
        hoverBackgroundColor: '#6F381A',
        borderRadius: { topLeft: 0, topRight: 0, bottomLeft: 4, bottomRight: 4 },
        stack: 'sentimentStack',
        maxBarThickness: 38,
      },
      {
        label: 'Neutral Feedback',
        data: daily.map((d) => d.neutral || 0),
        backgroundColor: '#C08A5B',
        hoverBackgroundColor: '#A87346',
        stack: 'sentimentStack',
        maxBarThickness: 38,
      },
      {
        label: 'Positive Experience',
        data: daily.map((d) => d.positive || 0),
        backgroundColor: '#52706A',
        hoverBackgroundColor: '#3B5550',
        borderRadius: { topLeft: 6, topRight: 6, bottomLeft: 0, bottomRight: 0 },
        stack: 'sentimentStack',
        maxBarThickness: 38,
      },
    ],
  };

  const histogramOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        align: 'end',
        labels: {
          boxWidth: 12,
          boxHeight: 12,
          usePointStyle: true,
          pointStyle: 'rectRounded',
          font: { size: 11, weight: 'bold' },
          color: '#334155',
          padding: 16,
        },
      },
      tooltip: {
        backgroundColor: '#3B1F12',
        titleFont: { size: 12, weight: 'bold' },
        bodyFont: { size: 11 },
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          afterTitle: (items) => {
            const idx = items[0]?.dataIndex;
            if (idx !== undefined && daily[idx]) {
              const sum = (daily[idx].positive || 0) + (daily[idx].neutral || 0) + (daily[idx].negative || 0);
              return `Total Volume: ${sum} feedback records`;
            }
            return '';
          },
        },
      },
    },
    scales: {
      x: {
        stacked: true,
        grid: { display: false },
        ticks: { color: '#64748B', font: { size: 11, weight: '600' } },
        title: { display: true, text: 'Service / Complaint Date (MM/DD)', color: '#6F4530', font: { weight: 'bold', size: 11 } },
      },
      y: {
        stacked: true,
        beginAtZero: true,
        ticks: { precision: 0, color: '#64748B', font: { size: 10 } },
        grid: { color: 'rgba(226, 232, 240, 0.7)' },
        title: { display: true, text: 'Total Complaints & Feedback Volume', color: '#6F4530', font: { weight: 'bold', size: 11 } },
      },
    },
  };

  return (
    <div className="mx-auto max-w-7xl space-y-7 text-slate-800">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#52706A]">
          Objective 3 & 4 · Trends & Emerging Failure Patterns
        </p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900 sm:text-3xl">
          Feedback Trends & Anomaly Histogram
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          Executive visualization of feedback volume, complaint surges, sentiment proportions, and severity distributions.
        </p>
      </header>

      {/* SUMMARY DISTRIBUTION CARDS */}
      <div className="grid gap-5 xl:grid-cols-2">
        {[['Sentiment', sentimentLabels], ['Severity', severityLabels]].map(([title, labels]) => (
          <section key={title} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">{title} Distribution</h2>
            <p className="mt-1 text-sm text-slate-500">{total.toLocaleString()} total analyzed feedback records</p>
            <div className="mt-5 space-y-4">
              {labels.map((label) => {
                const count = Number((title === 'Sentiment' ? sentiment : severity)[label] || 0);
                const percent = total ? ((count / total) * 100) : 0;
                const color = title === 'Sentiment'
                  ? colors[label]
                  : ({ low: '#52706A', medium: '#C08A5B', high: '#8B4F2C', critical: '#3B1F12' })[label];

                return (
                  <div key={label}>
                    <div className="mb-1.5 flex justify-between text-sm">
                      <span className="capitalize font-medium text-slate-700">{label}</span>
                      <span className="font-bold text-slate-900">
                        {count.toLocaleString()} · {percent.toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${percent}%`, backgroundColor: color }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        ))}
      </div>

      {/* HISTOGRAM CHART SECTION */}
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2.5">
            <BarChart3 className="h-6 w-6 text-[#6F4530]" />
            <div>
              <h2 className="text-lg font-bold text-slate-900">Daily Feedback Activity Histogram</h2>
              <p className="text-xs text-slate-500">Stacked by sentiment category to identify complaint surges</p>
            </div>
          </div>
          <div className="inline-flex items-center gap-1.5 rounded-lg bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-900">
            <HelpCircle className="h-3.5 w-3.5 text-amber-700" />
            Easy-to-read executive histogram
          </div>
        </div>

        {/* Chart Container */}
        {daily.length ? (
          <div className="mt-5">
            <div className="h-80 w-full" role="img" aria-label="Daily feedback activity histogram chart">
              <Bar data={histogramData} options={histogramOptions} />
            </div>

            {/* Non-technical user guide */}
            <div className="mt-4 flex items-start gap-2 rounded-lg bg-[#FAF6F0] p-3 text-xs leading-relaxed text-[#6F4530]">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-[#C08A5B]" />
              <span>
                <strong>How to interpret this histogram:</strong> The total height of each column shows how many customer feedback records arrived on that day. Dark brown blocks represent negative complaints, gold blocks represent neutral feedback, and green blocks represent positive reviews. A tall bar dominated by dark brown indicates an emerging technical defect spike.
              </span>
            </div>
          </div>
        ) : (
          <div className="mt-6 rounded-lg border border-dashed border-slate-200 bg-slate-50 px-6 py-14 text-center">
            <Info className="mx-auto h-6 w-6 text-[#52706A]" />
            <p className="mt-2 text-sm font-semibold text-slate-700">No daily trend data available</p>
            <p className="mt-1 text-xs text-slate-500">Upload customer feedback files with service dates to plot this histogram.</p>
          </div>
        )}
      </section>
    </div>
  );
}

export default TrendsAnalysis;
