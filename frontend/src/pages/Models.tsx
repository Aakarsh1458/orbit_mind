import React, { useState, useEffect } from 'react';
import { getModels, getProviders, validateProvider } from '../api/modelsApi';
import { LLMProviderStatus, SpecialistModelDetail } from '../types/api';
import { useOrbitStore } from '../store/useOrbitStore';
import { BrutalistBadge } from '../components/brutalist/BrutalistBadge';
import { BrutalistButton } from '../components/brutalist/BrutalistButton';
import { Cpu, Network, CheckCircle2, AlertTriangle, ShieldCheck, ArrowRight } from 'lucide-react';

export const Models: React.FC = () => {
  const { aiStatus } = useOrbitStore();
  const [models, setModels] = useState<SpecialistModelDetail[]>([]);
  const [providers, setProviders] = useState<LLMProviderStatus[]>([]);
  const [validatingProvider, setValidatingProvider] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<{ provider: string; status: string } | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [m, p] = await Promise.all([getModels(), getProviders()]);
        setModels(m || []);
        setProviders(p || []);
      } catch (err) {
        console.error('Failed to load models/providers:', err);
      }
    };
    load();
  }, []);

  const handleValidate = async (name: string) => {
    setValidatingProvider(name);
    setValidationResult(null);
    try {
      const res = await validateProvider(name);
      setValidationResult({
        provider: name,
        status: res.configured
          ? `CONFIGURED (Model: ${res.model || 'Default'})`
          : 'UNCONFIGURED (Credentials missing in .env)',
      });
    } catch (err: any) {
      setValidationResult({
        provider: name,
        status: `ERROR: ${err.message}`,
      });
    } finally {
      setValidatingProvider(null);
    }
  };

  return (
    <div className="relative z-10 max-w-7xl mx-auto px-4 py-8 space-y-10">
      {/* Top Header */}
      <div className="space-y-1 border-b border-space-border pb-5">
        <div className="flex items-center gap-2 font-mono text-xs text-electric-cyan uppercase">
          <Cpu className="w-4 h-4" />
          <span>AI SPECIALIST REGISTRY & ORCHESTRATION PIPELINES</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-mono font-bold text-white uppercase">
          MODEL ROUTING & INFERENCE INFRASTRUCTURE
        </h1>
        <p className="font-sans text-slate-300 text-sm max-w-2xl">
          Declarative remote-sensing neural architectures, LLM planners (NVIDIA Nemotron / OpenRouter), fallback heuristics, and device accelerators.
        </p>
      </div>

      {/* LLM Providers Section */}
      <div className="space-y-3 font-mono text-xs">
        <div className="flex items-center justify-between">
          <span className="font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
            <Network className="w-4 h-4 text-electric-cyan" />
            ORCHESTRATION LLM PROVIDERS
          </span>
          <span className="text-[10px] text-slate-400">// CREDENTIALS LOADED VIA ENVIRONMENT</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {providers.map((p) => (
            <div
              key={p.provider}
              className="bg-space-card border border-space-border p-3.5 space-y-2.5 shadow-brutal flex flex-col justify-between"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-slate-100 uppercase">{p.provider}</span>
                  {p.is_default && (
                    <BrutalistBadge variant="violet" size="sm">
                      DEFAULT ROUTE
                    </BrutalistBadge>
                  )}
                </div>

                <div className="flex items-center gap-2 text-[11px]">
                  <span
                    className={`w-2 h-2 ${
                      p.configured ? 'bg-radar-green' : 'bg-slate-600'
                    }`}
                  />
                  <span className="text-slate-300 font-semibold">
                    {p.configured ? 'CONFIGURED & READY' : 'NOT CONFIGURED'}
                  </span>
                </div>
              </div>

              <div className="pt-2 border-t border-space-border flex items-center justify-between">
                <button
                  onClick={() => handleValidate(p.provider)}
                  disabled={validatingProvider === p.provider}
                  className="px-2.5 py-1 bg-space-panel border border-space-border hover:border-electric-cyan text-slate-300 hover:text-white text-[10px] font-bold uppercase transition-colors"
                >
                  {validatingProvider === p.provider ? 'TESTING...' : 'VALIDATE ACCESS'}
                </button>
              </div>
            </div>
          ))}
        </div>

        {validationResult && (
          <div className="p-3 bg-space-dark border border-space-border text-xs flex items-center gap-2">
            <span className="font-bold text-electric-cyan uppercase">
              {validationResult.provider}:
            </span>
            <span className="text-slate-200">{validationResult.status}</span>
          </div>
        )}
      </div>

      {/* Model Routing Architecture Visual Diagram */}
      <div className="bg-space-dark border border-space-border p-6 shadow-brutal space-y-4 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-space-border pb-3">
          <span className="font-bold uppercase tracking-wider text-slate-200">
            TASK DECOMPOSITION & SPECIALIST ROUTING GRAPH
          </span>
          <span className="text-slate-400 text-[10px]">BOUNDED EXECUTION (MAX 8 STEPS)</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-center">
          <div className="bg-space-panel border border-space-border p-3 space-y-1">
            <span className="text-slate-400 text-[9px] uppercase block">STAGE 01</span>
            <span className="font-bold text-white text-xs">NATURAL LANGUAGE</span>
            <p className="text-[10px] font-sans text-slate-400">User prompts & temporal window</p>
          </div>

          <div className="bg-space-panel border border-electric-cyan/60 p-3 space-y-1 text-electric-cyan">
            <span className="text-slate-400 text-[9px] uppercase block">STAGE 02</span>
            <span className="font-bold text-xs">LLM TASK PLANNER</span>
            <p className="text-[10px] font-sans text-slate-400">Structured intent & input check</p>
          </div>

          <div className="bg-space-panel border border-electric-violet/60 p-3 space-y-1 text-electric-violet">
            <span className="text-slate-400 text-[9px] uppercase block">STAGE 03</span>
            <span className="font-bold text-xs">MODEL ROUTER</span>
            <p className="text-[10px] font-sans text-slate-400">Selects primary vs fallback model</p>
          </div>

          <div className="bg-space-panel border border-radar-green/60 p-3 space-y-1 text-radar-green">
            <span className="text-slate-400 text-[9px] uppercase block">STAGE 04</span>
            <span className="font-bold text-xs">EXECUTION & VALIDATION</span>
            <p className="text-[10px] font-sans text-slate-400">CRS, overlap, & GeoTIFF masks</p>
          </div>
        </div>
      </div>

      {/* Specialist Model Registry Table */}
      <div className="space-y-3 font-mono text-xs">
        <div className="flex items-center justify-between">
          <span className="font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-radar-green" />
            REGISTERED REMOTE SENSING SPECIALISTS ({models.length})
          </span>
          <span className="text-[10px] text-slate-400">// HARD FAILOVER GUARANTEED</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {models.map((m) => (
            <div
              key={m.id}
              className="bg-space-card border border-space-border p-4 space-y-3 shadow-brutal flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-slate-100">{m.id}</span>
                  <BrutalistBadge variant="violet" size="sm">
                    {m.task}
                  </BrutalistBadge>
                </div>

                <p className="font-sans text-slate-300 text-xs leading-relaxed">
                  {m.capabilities?.description || 'Remote-sensing machine learning model.'}
                </p>

                <div className="pt-2 border-t border-space-border space-y-1 text-[10px] text-slate-400">
                  <div>
                    MODALITIES:{' '}
                    <span className="text-slate-200 uppercase font-semibold">
                      {m.capabilities?.modalities?.join(', ') || 'OPTICAL'}
                    </span>
                  </div>
                  <div>
                    INPUT REQUIREMENTS:{' '}
                    <span className="text-slate-200">
                      {m.capabilities?.min_rasters} to {m.capabilities?.max_rasters} temporal scenes
                    </span>
                  </div>
                  {m.fallback_model_id && (
                    <div>
                      FALLBACK MODEL:{' '}
                      <span className="text-radar-amber font-semibold">{m.fallback_model_id}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-2 border-t border-space-border flex items-center justify-between text-[10px]">
                <span className="text-slate-400">STATUS:</span>
                <span className="text-radar-green font-bold">● REGISTERED & AVAILABLE</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
