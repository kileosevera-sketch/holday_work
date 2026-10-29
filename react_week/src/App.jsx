import { useCallback, useEffect, useState } from 'react';
import Sidebar from './components/sidebar';
import DashCards from './components/dashcards';
import Analysis from './components/Analysis';
import TrendsAnalysis from './components/trendsanalysis';
import FeedbackHistory from './components/FeedbackHistory';
import EarlyWarnings from './components/EarlyWarnings';
import AIInsights from './components/AIInsights';
import { fetchDashboardData } from './api';

function App() {
  const [currentTab, setCurrentTab] = useState('Home');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [dashboardData, setDashboardData] = useState({
    summary: { total_feedback: 0, sentiment: {}, severity: {}, causes: [], daily: [] },
    feedback: { items: [], total: 0 }, reports: [], alerts: [], predictions: [],
  });
  const [connection, setConnection] = useState('loading');
  const [loadError, setLoadError] = useState('');

  const refreshData = useCallback(async () => {
    try {
      const data = await fetchDashboardData();
      setDashboardData(data);
      setConnection('connected');
      setLoadError('');
      return data;
    } catch (error) {
      setConnection('disconnected');
      setLoadError(error.message);
      throw error;
    }
  }, []);

  useEffect(() => {
    let active = true;
    fetchDashboardData().then(data => {
      if (!active) return;
      setDashboardData(data);
      setConnection('connected');
      setLoadError('');
    }).catch(error => {
      if (!active) return;
      setConnection('disconnected');
      setLoadError(error.message);
    });
    return () => { active = false; };
  }, []);

  const handleUploadComplete = async () => {
    setCurrentTab('Analyze');
    try { await refreshData(); } catch { /* The upload itself has already succeeded. */ }
  };

  return (
    <div className={`dashboard-theme ${isDarkMode ? 'theme-dark' : 'theme-light'} relative isolate flex min-h-screen flex-col bg-[#F4F7F4] md:flex-row`}>
      <div className="dashboard-background-rings" aria-hidden="true">
        <svg
          className="dashboard-background-rings__art"
          viewBox="0 0 1440 960"
          preserveAspectRatio="xMidYMid slice"
          fill="none"
        >
          <g stroke="currentColor" strokeWidth="4">
            <circle cx="1150" cy="210" r="240" />
            <circle cx="1150" cy="210" r="400" />
            <circle cx="1150" cy="210" r="560" />
            <circle cx="240" cy="790" r="300" />
            <circle cx="240" cy="790" r="500" />
          </g>
        </svg>
      </div>
      
      {/* SIDEBAR NAVIGATION */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapsed={() => setIsSidebarCollapsed((collapsed) => !collapsed)}
        isDarkMode={isDarkMode}
        onToggleTheme={() => setIsDarkMode((darkMode) => !darkMode)}
      />

      {/* MAIN CONTENT AREA */}
      <main className="relative z-10 min-w-0 flex-1 overflow-y-auto px-4 py-5 sm:px-6 sm:py-7 lg:px-10 lg:py-9">
        <div className={`mb-5 flex items-center justify-between gap-3 rounded-lg px-4 py-2.5 text-xs ${connection === 'connected' ? 'bg-emerald-50 text-emerald-800' : connection === 'loading' ? 'bg-slate-100 text-slate-600' : 'bg-rose-50 text-rose-800'}`} role="status">
          <span>{connection === 'connected' ? `Backend connected · ${dashboardData.summary.total_feedback} saved feedback records` : connection === 'loading' ? 'Connecting to feedback backend…' : `Backend unavailable · ${loadError}`}</span>
          {connection === 'disconnected' && <button type="button" onClick={() => refreshData().catch(() => {})} className="font-semibold underline">Retry</button>}
        </div>
        
        {/* Page 1: Home */}
        {currentTab === 'Home' && (
          <DashCards 
            onNavigateToAnalyze={() => setCurrentTab('Analyze')} 
            onUploadComplete={handleUploadComplete}
            feedback={dashboardData.feedback.items}
            feedbackTotal={dashboardData.feedback.total}
            summary={dashboardData.summary}
          />
        )}

        {/* Page 2: Analyze */}
        {currentTab === 'Analyze' && (
          <Analysis summary={dashboardData.summary} feedback={dashboardData.feedback.items} />
        )}

        {/* Page 3: Trends Analysis */}
        {currentTab === 'Trends Analysis' && (
          <TrendsAnalysis data={{ totalFeedback: dashboardData.summary.total_feedback, sentiment: dashboardData.summary.sentiment, severity: dashboardData.summary.severity, daily: dashboardData.summary.daily }} />
        )}

        {/* Page 4: Feedback History */}
        {currentTab === 'Feedback History' && (
          <FeedbackHistory reports={dashboardData.reports} onRefresh={() => refreshData().catch(() => {})} />
        )}

        {currentTab === 'Early Warnings' && (
          <EarlyWarnings alerts={dashboardData.alerts} />
        )}

        {currentTab === 'AI Insights' && (
          <AIInsights predictions={dashboardData.predictions} feedback={dashboardData.feedback.items} />
        )}

      </main>

    </div>
  );
}

export default App;
