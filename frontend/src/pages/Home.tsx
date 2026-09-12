import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useOrbitStore } from '../store/useOrbitStore';
import { BrutalistButton } from '../components/brutalist/BrutalistButton';
import { BrutalistBadge } from '../components/brutalist/BrutalistBadge';
import { Globe, ArrowRight, Layers, Eye, ShieldCheck, Terminal, Cpu } from 'lucide-react';

export const Home: React.FC = () => {
  const navigate = useNavigate();
  const { aiStatus, executePrompt } = useOrbitStore();

  const handleLaunchSample = (query: string) => {
    navigate('/workspace');
    setTimeout(() => {
      executePrompt(query);
    }, 150);
  };

  const isMock = aiStatus?.ai_mode === 'mock';

  return (
    <div className="relative z-10 max-w-7xl mx-auto px-4 py-8 md:py-16 space-y-16">
      {/* Hero Section */}
      <div className="space-y-6">
        {/* Mission Telemetry Top Header */}
        <div className="flex flex-wrap items-center gap-3 font-mono text-xs select-none">
          <div className="flex items-center gap-2 px-2.5 py-1 bg-space-dark border border-space-border">
            <span className="w-2 h-2 bg-electric-cyan animate-pulse" />
            <span className="text-slate-300 font-bold uppercase">GROUND STATION ONLINE</span>
          </div>

          <BrutalistBadge variant={isMock ? 'amber' : 'green'} dot>
            {isMock ? 'AI CALIBRATION (MOCK MODE)' : 'LIVE AI INFERENCE'}
          </BrutalistBadge>

          <div className="hidden sm:flex items-center gap-2 text-slate-400">
            <span>SENSORS: OPTICAL + SAR</span>
            <span>//</span>
            <span>PROJECTION: EPSG:4326</span>
          </div>
        </div>

        {/* Massive Brutalist Heading */}
        <div className="space-y-2">
          <h1 className="text-5xl sm:text-7xl lg:text-8xl font-mono font-extrabold tracking-tight text-white uppercase select-none leading-none">
            ASK THE <span className="text-transparent bg-clip-text bg-gradient-to-r from-electric-violet via-electric-cyan to-white">PLANET.</span>
          </h1>
          <p className="text-xl sm:text-2xl font-sans text-slate-300 max-w-3xl leading-relaxed pt-2">
            Turn natural-language questions into autonomous satellite analysis, bitemporal change detection, and verifiable geospatial evidence.
          </p>
        </div>

        {/* Mission HUD Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs pt-4">
          <div className="bg-space-dark border border-space-border p-3 shadow-brutal">
            <span className="text-[10px] text-slate-400 block uppercase">ORBITAL TARGET</span>
            <span className="text-slate-100 font-bold text-sm">12.9716° N / 77.5946° E</span>
          </div>

          <div className="bg-space-dark border border-space-border p-3 shadow-brutal">
            <span className="text-[10px] text-slate-400 block uppercase">ACTIVE CONSTELLATIONS</span>
            <span className="text-electric-cyan font-bold text-sm">SENTINEL-1 / 2 // LANDSAT</span>
          </div>

          <div className="bg-space-dark border border-space-border p-3 shadow-brutal">
            <span className="text-[10px] text-slate-400 block uppercase">DEFAULT LLM ROUTER</span>
            <span className="text-electric-violet font-bold text-sm">
              {aiStatus?.llm?.default_provider ? aiStatus.llm.default_provider.toUpperCase() : 'NEMOTRON'}
            </span>
          </div>

          <div className="bg-space-dark border border-space-border p-3 shadow-brutal">
            <span className="text-[10px] text-slate-400 block uppercase">COMPUTE ACCELERATOR</span>
            <span className="text-radar-green font-bold text-sm">
              {aiStatus?.device ? aiStatus.device.toUpperCase() : 'CPU'}
            </span>
          </div>
        </div>

        {/* Primary CTAs */}
        <div className="flex flex-wrap items-center gap-4 pt-4">
          <Link to="/workspace">
            <BrutalistButton variant="cyan" size="lg" icon={<Terminal className="w-4 h-4" />}>
              ENTER COMMAND WORKSPACE
            </BrutalistButton>
          </Link>

          <Link to="/satellites">
            <BrutalistButton variant="secondary" size="lg" icon={<Globe className="w-4 h-4" />}>
              EXPLORE SATELLITE CATALOG
            </BrutalistButton>
          </Link>
        </div>
      </div>

      {/* Preset Analysis Query Starters */}
      <div className="bg-space-card/80 border border-space-border p-6 space-y-4 shadow-brutal">
        <div className="flex items-center justify-between border-b border-space-border pb-3 font-mono text-xs">
          <span className="font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-electric-cyan" />
            DIRECT COMMAND EXAMPLES
          </span>
          <span className="text-slate-400 text-[10px]">// CLICK TO LAUNCH LIVE ANALYSIS</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
          {[
            {
              title: 'URBAN EXPANSION 2022 → 2025',
              desc: 'Where did urban expansion occur between 2022 and 2025?',
              task: 'change_detection',
            },
            {
              title: 'VEGETATION MONITORING',
              desc: 'Detect vegetation loss and canopy deforestation in this region.',
              task: 'change_detection',
            },
            {
              title: 'LAND COVER SEGMENTATION',
              desc: 'Classify water bodies, built-up surfaces, and barren land.',
              task: 'segmentation',
            },
            {
              title: 'RADAR BACKSCATTER FUSION',
              desc: 'Compare optical RGB and Sentinel-1 SAR backscatter for flood inundation.',
              task: 'optical_sar',
            },
          ].map((item, idx) => (
            <div
              key={idx}
              onClick={() => handleLaunchSample(item.desc)}
              className="p-3.5 bg-space-dark border border-space-border hover:border-electric-cyan/80 cursor-pointer group transition-all shadow-brutal hover:translate-x-0.5 hover:translate-y-0.5 flex items-center justify-between"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-electric-cyan font-bold text-xs">{item.title}</span>
                  <BrutalistBadge variant="neutral" size="sm">
                    {item.task}
                  </BrutalistBadge>
                </div>
                <p className="text-slate-300 font-sans text-xs">{item.desc}</p>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-electric-cyan group-hover:translate-x-1 transition-all shrink-0 ml-3" />
            </div>
          ))}
        </div>
      </div>

      {/* Architecture Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
        <div className="bg-space-card/80 border border-space-border p-5 space-y-2 shadow-brutal">
          <div className="w-8 h-8 bg-electric-violet/20 border border-electric-violet flex items-center justify-center text-electric-violet mb-2">
            <Cpu className="w-4 h-4" />
          </div>
          <h3 className="font-bold text-sm text-slate-100 uppercase">AI ORCHESTRATION ENGINE</h3>
          <p className="font-sans text-slate-300 leading-relaxed text-xs">
            Autonomous query decomposition, task routing, step-budget safety policies, and automatic model failover between primary specialists and baseline heuristics.
          </p>
        </div>

        <div className="bg-space-card/80 border border-space-border p-5 space-y-2 shadow-brutal">
          <div className="w-8 h-8 bg-electric-cyan/20 border border-electric-cyan flex items-center justify-center text-electric-cyan mb-2">
            <Layers className="w-4 h-4" />
          </div>
          <h3 className="font-bold text-sm text-slate-100 uppercase">MAPLIBRE WEBGL GEOSPATIAL</h3>
          <p className="font-sans text-slate-300 leading-relaxed text-xs">
            Direct spatial rendering of GeoJSON vector polygons, bitemporal split-screen comparison sliders, and dynamic CRS reprojection via Rasterio and GDAL.
          </p>
        </div>

        <div className="bg-space-card/80 border border-space-border p-5 space-y-2 shadow-brutal">
          <div className="w-8 h-8 bg-radar-green/20 border border-radar-green flex items-center justify-center text-radar-green mb-2">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <h3 className="font-bold text-sm text-slate-100 uppercase">GROUND-TRUTH EVIDENCE</h3>
          <p className="font-sans text-slate-300 leading-relaxed text-xs">
            Every analysis answer is strictly anchored in quantified spatial statistics (area in km², pixel counts) and downloadable georeferenced GeoTIFF artifacts.
          </p>
        </div>
      </div>
    </div>
  );
};
