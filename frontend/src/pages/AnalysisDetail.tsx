import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getJobStatus, getAnalysisResult, getDownloadUrl } from '../api/analysisApi';
import { AnalysisJobItem, AnalysisResultResponse } from '../types/api';
import { BrutalistBadge } from '../components/brutalist/BrutalistBadge';
import { BrutalistButton } from '../components/brutalist/BrutalistButton';
import { ArrowLeft, Download, ShieldCheck, Activity, Terminal, Clock, FileCheck } from 'lucide-react';
import { EarthMap } from '../components/map/EarthMap';

export const AnalysisDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<AnalysisJobItem | null>(null);
  const [result, setResult] = useState<AnalysisResultResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const fetchDetail = async () => {
      setLoading(true);
      try {
        const j = await getJobStatus(id);
        setJob(j);

        if (j.status === 'completed') {
          const r = await getAnalysisResult(id);
          setResult(r);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to fetch job');
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center font-mono text-xs text-slate-400 space-y-2">
        <span className="w-3 h-3 bg-electric-cyan animate-ping" />
        <div>RETRIEVING MISSION LOGS FOR JOB // {id}</div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 font-mono text-xs space-y-4">
        <div className="p-4 bg-radar-red/15 border border-radar-red text-radar-red">
          JOB AUDIT ERROR: {error || 'Record not found.'}
        </div>
        <Link to="/history">
          <BrutalistButton variant="secondary" size="sm" icon={<ArrowLeft className="w-3 h-3" />}>
            BACK TO MISSION ARCHIVE
          </BrutalistButton>
        </Link>
      </div>
    );
  }

  const isMock = result?.mode === 'mock';

  return (
    <div className="relative z-10 max-w-7xl mx-auto px-4 py-8 space-y-8 font-mono text-xs">
      {/* Top Header & Breadcrumbs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-space-border pb-4">
        <div className="flex items-center gap-3">
          <Link to="/history">
            <BrutalistButton variant="secondary" size="sm" icon={<ArrowLeft className="w-3.5 h-3.5" />}>
              ARCHIVE
            </BrutalistButton>
          </Link>
          <div>
            <div className="text-[10px] text-slate-400 uppercase">JOB ID // {job.job_id}</div>
            <h1 className="text-xl font-bold text-white uppercase">
              {job.query || `${job.analysis_type.toUpperCase()} ANALYSIS`}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <BrutalistBadge variant={job.status === 'completed' ? 'green' : 'red'}>
            STATUS: {job.status.toUpperCase()}
          </BrutalistBadge>
          <BrutalistBadge variant={isMock ? 'amber' : 'green'}>
            {isMock ? 'CALIBRATION MODE' : 'LIVE SATELLITE DATA'}
          </BrutalistBadge>
        </div>
      </div>

      {/* Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-space-card border border-space-border p-4 space-y-1 shadow-brutal">
          <span className="text-[10px] text-slate-400 uppercase block">ANALYSIS PIPELINE</span>
          <span className="text-sm font-bold text-electric-cyan uppercase">
            {job.analysis_type}
          </span>
          <div className="text-[10px] text-slate-400 pt-1">
            CREATED: {new Date(job.created_at).toLocaleString()}
          </div>
        </div>

        <div className="bg-space-card border border-space-border p-4 space-y-1 shadow-brutal">
          <span className="text-[10px] text-slate-400 uppercase block">EXECUTION CONFIDENCE</span>
          <span className="text-sm font-bold text-radar-green">
            {result?.confidence !== undefined && result.confidence !== null
              ? `${Math.round(result.confidence * 100)}% VERIFIED`
              : 'CONFIDENCE N/A'}
          </span>
          <div className="text-[10px] text-slate-400 pt-1">GROUND TRUTH VALIDATED</div>
        </div>

        <div className="bg-space-card border border-space-border p-4 space-y-1 shadow-brutal">
          <span className="text-[10px] text-slate-400 uppercase block">QUANTIFIED AREA</span>
          <span className="text-sm font-bold text-electric-violet">
            {result?.statistics?.area_km2 !== undefined
              ? `${result.statistics.area_km2.toFixed(2)} km²`
              : 'N/A'}
          </span>
          <div className="text-[10px] text-slate-400 pt-1">
            {result?.statistics?.changed_pixels !== undefined
              ? `${result.statistics.changed_pixels.toLocaleString()} CHANGED PIXELS`
              : 'RASTER EXTRACTION'}
          </div>
        </div>
      </div>

      {/* Summary Narrative */}
      {result?.summary && (
        <div className="bg-space-dark border border-space-border p-4 space-y-2">
          <span className="text-[10px] text-slate-400 uppercase font-bold">
            EXECUTIVE FINDINGS // RESULT NARRATIVE:
          </span>
          <p className="font-sans text-sm text-slate-100 leading-relaxed">
            {result.summary}
          </p>
        </div>
      )}

      {/* Evidence and Downloads */}
      {result?.evidence && Object.keys(result.evidence).length > 0 && (
        <div className="bg-space-card border border-space-border p-4 space-y-3 shadow-brutal">
          <span className="text-xs uppercase font-bold text-slate-200 flex items-center gap-2 border-b border-space-border pb-2">
            <FileCheck className="w-4 h-4 text-electric-cyan" />
            GROUND-TRUTH EVIDENCE ARTIFACTS
          </span>

          <div className="space-y-2">
            {Object.entries(result.evidence).map(([key, val]) => (
              <div
                key={key}
                className="flex items-center justify-between p-2.5 bg-space-dark border border-space-border"
              >
                <div>
                  <span className="font-bold text-slate-200 uppercase">{key}</span>
                  <div className="text-[10px] text-slate-400 truncate max-w-md">
                    {typeof val === 'string' ? val : JSON.stringify(val)}
                  </div>
                </div>

                {typeof val === 'string' && val.endsWith('.tif') && (
                  <a
                    href={getDownloadUrl(job.job_id, val.split('/').pop() || val)}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1 bg-electric-cyan text-space-black font-bold uppercase text-[10px] flex items-center gap-1.5 shadow-brutal-cyan"
                  >
                    <Download className="w-3 h-3" />
                    <span>DOWNLOAD GEOTIFF</span>
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Execution Trace Steps */}
      {result?.execution_trace && result.execution_trace.length > 0 && (
        <div className="bg-space-card border border-space-border p-4 space-y-2 shadow-brutal">
          <span className="text-xs uppercase font-bold text-slate-200 flex items-center gap-2 border-b border-space-border pb-2">
            <Clock className="w-4 h-4 text-slate-400" />
            ORCHESTRATION STEP TRACE
          </span>
          <div className="flex flex-wrap gap-2 pt-1">
            {result.execution_trace.map((tr: string, idx: number) => (
              <span
                key={idx}
                className="px-2 py-1 bg-space-dark border border-space-border text-slate-300 text-[10px] uppercase font-mono"
              >
                {idx + 1}. {tr}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
