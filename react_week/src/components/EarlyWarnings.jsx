import { AlertOctagon, Bell, CheckCircle2, ShieldAlert, TrendingUp, Zap } from 'lucide-react';

function EarlyWarnings({ alerts = [] }) {
  const criticalCount = alerts
    .filter((alert) => alert.severity === 'critical')
    .reduce((sum, alert) => sum + alert.count, 0);
  const totalCount = alerts.reduce((sum, alert) => sum + alert.count, 0);

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-wider text-[#965228]">
          Objective 8 · Automated Anomaly & Early Warning Detection
        </p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900 sm:text-3xl">
          Early Warnings & Emerging Failure Alerts
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          Proactively identify unusual surges in severe complaints before widespread product recalls or major churn.
        </p>
      </header>

      {/* METRIC COUNTERS */}
      <div className="grid gap-5 md:grid-cols-3">
        {[
          { label: 'Critical Safety / Urgent Alerts', value: criticalCount, icon: AlertOctagon, color: 'text-rose-700 bg-rose-50 border-rose-200' },
          { label: 'Total High Priority Issues', value: totalCount, icon: TrendingUp, color: 'text-orange-700 bg-orange-50 border-orange-200' },
          { label: 'Active Risk Categories', value: alerts.length, icon: ShieldAlert, color: 'text-amber-700 bg-amber-50 border-amber-200' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className={`flex items-center gap-4 rounded-xl border p-5 shadow-sm ${color}`}>
            <span className="rounded-xl bg-white p-3 shadow-xs">
              <Icon className="h-6 w-6" />
            </span>
            <div>
              <p className="text-xs uppercase font-bold tracking-wider">{label}</p>
              <p className="text-2xl font-bold text-slate-900">{value.toLocaleString()}</p>
            </div>
          </div>
        ))}
      </div>

      {/* PRIORITIZED FAILURE CATEGORIES */}
      <section className="rounded-xl border border-amber-200 bg-[#fffdfa] p-6 shadow-sm">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-amber-100 pb-4">
          <div className="flex items-center gap-2.5">
            <Bell className="h-5 w-5 text-amber-800" />
            <div>
              <h2 className="text-lg font-bold text-slate-900">Prioritized Technical Failure Alerts</h2>
              <p className="text-xs text-slate-500">Sorted by severity impact and recurrence frequency</p>
            </div>
          </div>
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-900">
            {alerts.length} Active Early Warnings
          </span>
        </div>

        <div className="space-y-3.5">
          {alerts.map((item, index) => {
            const isCrit = item.severity === 'critical';
            return (
              <article key={`${item.cause}-${item.severity}`} className="rounded-xl border border-amber-100 bg-white p-5 shadow-xs">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className={`rounded-md px-2.5 py-1 text-xs font-bold uppercase text-white ${
                      isCrit ? 'bg-rose-800' : 'bg-orange-600'
                    }`}>
                      {item.severity}
                    </span>
                    <h3 className="font-bold text-base text-slate-900">{item.cause.replaceAll('_', ' ')}</h3>
                  </div>
                  <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-bold text-amber-900 border border-amber-200">
                    {item.count} complaints logged
                  </span>
                </div>

                <p className="mt-3 text-sm text-slate-600 leading-relaxed">
                  <strong>Risk Assessment:</strong> {item.count} customer complaint records have been classified as{' '}
                  <span className="font-semibold text-slate-800">{item.severity} severity</span>. Immediate engineering inspection is advised to prevent field warranty spikes.
                </p>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-3 text-xs text-slate-500">
                  <span className="inline-flex items-center gap-1 text-[#6F4530] font-semibold">
                    <Zap className="h-3.5 w-3.5" /> Recommended Action: Quality assurance verification & firmware/part trace
                  </span>
                  <span className="font-medium text-slate-400">Priority Level #{index + 1}</span>
                </div>
              </article>
            );
          })}

          {!alerts.length && (
            <div className="py-14 text-center">
              <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-600" />
              <p className="mt-3 font-semibold text-slate-800">No Critical Early Warnings</p>
              <p className="mt-1 text-xs text-slate-500">No customer feedback records currently meet the high or critical risk thresholds.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export default EarlyWarnings;
