import React, { useState, useEffect } from 'react';
import { listJobs } from '../api/analysisApi';
import { listConversations } from '../api/conversationsApi';
import { AnalysisJobItem, ConversationSummary } from '../types/api';
import { BrutalistBadge } from '../components/brutalist/BrutalistBadge';
import { BrutalistButton } from '../components/brutalist/BrutalistButton';
import { History as HistoryIcon, ArrowUpRight, MessageSquare, Activity, RefreshCw } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useOrbitStore } from '../store/useOrbitStore';

export const History: React.FC = () => {
  const navigate = useNavigate();
  const { setConversationId } = useOrbitStore();
  const [activeTab, setActiveTab] = useState<'jobs' | 'conversations'>('jobs');
  const [jobs, setJobs] = useState<AnalysisJobItem[]>([]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [j, c] = await Promise.allSettled([listJobs(50, 0), listConversations(50, 0)]);
      if (j.status === 'fulfilled') setJobs(j.value || []);
      if (c.status === 'fulfilled') setConversations(c.value || []);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleResumeConversation = (convId: string) => {
    setConversationId(convId);
    navigate('/workspace');
  };

  return (
    <div className="relative z-10 max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-space-border pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2 font-mono text-xs text-electric-cyan uppercase">
            <HistoryIcon className="w-4 h-4" />
            <span>MISSION ARCHIVES & INFERENCE RUN LOGS</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-mono font-bold text-white uppercase">
            ANALYSIS RUN ARCHIVE
          </h1>
          <p className="font-sans text-slate-300 text-sm max-w-2xl">
            Audit trail of all executed earth-observation analysis jobs, spatial evidence, and multi-turn operator conversations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <BrutalistButton
            variant="secondary"
            size="sm"
            onClick={loadData}
            icon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />}
          >
            REFRESH LOGS
          </BrutalistButton>
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="flex items-center gap-2 border-b border-space-border pb-1 font-mono text-xs select-none">
        <button
          onClick={() => setActiveTab('jobs')}
          className={`px-4 py-2 border transition-colors flex items-center gap-2 ${
            activeTab === 'jobs'
              ? 'bg-space-dark border-electric-cyan text-electric-cyan font-bold shadow-brutal-cyan'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>ANALYSIS JOBS ({jobs.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('conversations')}
          className={`px-4 py-2 border transition-colors flex items-center gap-2 ${
            activeTab === 'conversations'
              ? 'bg-space-dark border-electric-violet text-electric-violet font-bold shadow-brutal'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <MessageSquare className="w-3.5 h-3.5" />
          <span>CONVERSATION SESSIONS ({conversations.length})</span>
        </button>
      </div>

      {/* Jobs Log View */}
      {activeTab === 'jobs' && (
        <div className="space-y-3 font-mono text-xs">
          {jobs.length === 0 ? (
            <div className="p-8 text-center bg-space-dark border border-space-border text-slate-500">
              No asynchronous analysis jobs logged yet. Submit an analysis job from the workspace or API.
            </div>
          ) : (
            <div className="border border-space-border overflow-x-auto shadow-brutal bg-space-card">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-space-panel/90 border-b border-space-border text-[10px] text-slate-400 uppercase">
                    <th className="p-3">STATUS</th>
                    <th className="p-3">QUERY / OBJECTIVE</th>
                    <th className="p-3">TASK</th>
                    <th className="p-3">JOB ID</th>
                    <th className="p-3">PROGRESS</th>
                    <th className="p-3">CREATED</th>
                    <th className="p-3 text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-space-border">
                  {jobs.map((job) => {
                    const isDone = job.status === 'completed';
                    const isFailed = job.status === 'failed';
                    return (
                      <tr
                        key={job.job_id}
                        className="hover:bg-space-panel/40 transition-colors text-slate-300"
                      >
                        <td className="p-3">
                          <BrutalistBadge
                            variant={isDone ? 'green' : isFailed ? 'red' : 'violet'}
                            size="sm"
                            dot={!isDone}
                          >
                            {job.status}
                          </BrutalistBadge>
                        </td>
                        <td className="p-3 font-semibold text-slate-100 max-w-xs truncate">
                          {job.query || 'Direct task submission'}
                        </td>
                        <td className="p-3 uppercase text-electric-cyan">{job.analysis_type}</td>
                        <td className="p-3 text-[11px] text-slate-400 font-mono">
                          {job.job_id.substring(0, 8)}...
                        </td>
                        <td className="p-3">{Math.round(job.progress * 100)}%</td>
                        <td className="p-3 text-[10px] text-slate-400">
                          {new Date(job.created_at).toLocaleString()}
                        </td>
                        <td className="p-3 text-right">
                          <Link
                            to={`/analysis/${job.job_id}`}
                            className="inline-flex items-center gap-1 px-2.5 py-1 bg-space-dark border border-space-border hover:border-electric-cyan text-slate-300 hover:text-white uppercase font-bold text-[10px]"
                          >
                            <span>INSPECT</span>
                            <ArrowUpRight className="w-3 h-3" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Conversations Session View */}
      {activeTab === 'conversations' && (
        <div className="space-y-3 font-mono text-xs">
          {conversations.length === 0 ? (
            <div className="p-8 text-center bg-space-dark border border-space-border text-slate-500">
              No previous conversation sessions recorded.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {conversations.map((c) => (
                <div
                  key={c.conversation_id}
                  onClick={() => handleResumeConversation(c.conversation_id)}
                  className="p-4 bg-space-card border border-space-border hover:border-electric-violet cursor-pointer transition-all shadow-brutal flex items-center justify-between group"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-slate-100 group-hover:text-electric-violet transition-colors">
                        {c.title || 'Satellite Conversation'}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400">
                      SESSION ID: {c.conversation_id.substring(0, 12)}...
                    </div>
                    <div className="text-[10px] text-slate-400">
                      LAST ACTIVE: {new Date(c.updated_at).toLocaleString()}
                    </div>
                  </div>

                  <span className="text-xs uppercase font-bold text-slate-500 group-hover:text-electric-violet">
                    [ RESUME ]
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
