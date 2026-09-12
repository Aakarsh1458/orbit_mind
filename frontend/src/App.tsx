import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useOrbitStore } from './store/useOrbitStore';
import { TopNav } from './components/navigation/TopNav';
import { SystemStatusBar } from './components/navigation/SystemStatusBar';
import { Workspace } from './pages/Workspace';
import { Home } from './pages/Home';
import { Satellites } from './pages/Satellites';
import { Models } from './pages/Models';
import { History } from './pages/History';
import { AnalysisDetail } from './pages/AnalysisDetail';

export const App: React.FC = () => {
  const { fetchSystemStatus, fetchImagery } = useOrbitStore();

  useEffect(() => {
    fetchSystemStatus();
    fetchImagery();
  }, [fetchSystemStatus, fetchImagery]);

  return (
    <BrowserRouter>
      <div className="relative min-h-screen flex flex-col font-sans bg-[#050508] text-[#f8fafc] selection:bg-purple-600 selection:text-white">
        {/* Deep Cosmos Top Navigation Bar */}
        <TopNav />

        {/* Core Workspace & Application Views */}
        <main className="relative z-10 flex-1 flex flex-col overflow-hidden">
          <Routes>
            <Route path="/" element={<Workspace />} />
            <Route path="/workspace" element={<Workspace />} />
            <Route path="/observatory" element={<Home />} />
            <Route path="/satellites" element={<Satellites />} />
            <Route path="/models" element={<Models />} />
            <Route path="/history" element={<History />} />
            <Route path="/analysis/:id" element={<AnalysisDetail />} />
            <Route path="*" element={<Workspace />} />
          </Routes>
        </main>

        {/* Real-time Subsystem & Cursor Telemetry Footer */}
        <SystemStatusBar />
      </div>
    </BrowserRouter>
  );
};

export default App;
