import React, { useState } from 'react';
import { useOrbitStore } from '../../store/useOrbitStore';
import { BrutalistButton } from '../brutalist/BrutalistButton';
import { Send, Image, Layers, Sparkles, Database, Play } from 'lucide-react';
import { loadDatasetSample } from '../../api/datasetApi';

const PRESET_QUERIES = [
  'Where did urban expansion occur between 2022 and 2025?',
  'Detect vegetation loss and deforestation in this region.',
  'Analyze land cover composition and water bodies.',
  'Inspect radar backscatter and identify flooded areas.',
];

export const ChatInput: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [loadingDataset, setLoadingDataset] = useState(false);
  const {
    executePrompt,
    isExecuting,
    imageryList,
    selectedImageryIds,
    activeImageryId,
    setActiveImageryId,
    toggleImagerySelection,
    fetchImagery,
    setSelectedImageryIds,
    addMessage,
  } = useOrbitStore();
  const [showImageSelector, setShowImageSelector] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isExecuting) return;
    executePrompt(prompt.trim());
    setPrompt('');
  };

  const handleSelectPreset = (text: string) => {
    setPrompt(text);
  };

  const handleRunAll6Models = () => {
    executePrompt(
      'Perform all 6 remote sensing models: segmentation, change detection, captioning, vqa, optical-sar fusion, and cloud removal on this imagery'
    );
  };

  const handleLoadSen12mscr = async () => {
    if (loadingDataset || isExecuting) return;
    try {
      setLoadingDataset(true);
      const res = await loadDatasetSample(0);
      await fetchImagery();
      if (res.imagery_ids && res.imagery_ids.length > 0) {
        setSelectedImageryIds(res.imagery_ids.slice(0, 2));
      } else if (res.optical_imagery_id) {
        setSelectedImageryIds([res.optical_imagery_id, res.sar_imagery_id].filter(Boolean));
      }
      addMessage({
        id: `sen12ms_${Date.now()}`,
        role: 'assistant',
        content: `🛰️ Hermanni/sen12mscr Benchmark Sample #0 Loaded:\n• Sentinel-2 Optical (13 Spectral Bands GeoTIFF)\n• Sentinel-1 SAR (2 Polarizations VV/VH GeoTIFF)\n• Cloud-Free Ground Truth Target\nDatasets are attached as active inputs. Ready to run the 6-model specialist suite.`,
        timestamp: new Date().toLocaleTimeString(),
        responsePayload: {
          request_id: 'sen12mscr_0',
          conversation_id: 'benchmark',
          status: 'completed',
          answer: 'SEN12MS-CR benchmark sample loaded successfully.',
          follow_up_suggestions: [
            'Perform all 6 remote sensing models',
            'Run cloud removal with SAR radar fusion',
            'Run land cover semantic segmentation',
            'Detect bi-temporal SAR change anomalies',
          ],
        },
      });
    } catch (err: any) {
      console.error('Failed to load dataset sample:', err);
      addMessage({
        id: `err_${Date.now()}`,
        role: 'assistant',
        content: `⚠️ Failed to load Hermanni/sen12mscr benchmark sample: ${err.message}`,
        timestamp: new Date().toLocaleTimeString(),
      });
    } finally {
      setLoadingDataset(false);
    }
  };

  return (
    <div className="border-t border-space-border bg-space-card/95 p-3 space-y-2.5 select-none">
      {/* Quick Prompt Presets */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar text-[11px] font-mono">
        <span className="text-slate-400 shrink-0 text-[10px] uppercase">// PRESETS:</span>
        {PRESET_QUERIES.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSelectPreset(q)}
            className="shrink-0 px-2 py-0.5 bg-space-panel/80 hover:bg-space-panel border border-space-border hover:border-slate-500 text-slate-300 transition-colors truncate max-w-[200px]"
            title={q}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Action Controls & Selected Imagery Chips */}
      <div className="flex items-center justify-between font-mono text-xs flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={() => setShowImageSelector(!showImageSelector)}
            className="px-2 py-1 bg-space-panel border border-space-border hover:border-electric-cyan text-slate-300 hover:text-white flex items-center gap-1.5 text-[11px]"
          >
            <Image className="w-3 h-3 text-electric-cyan" />
            <span>
              IMAGERY INPUTS ({selectedImageryIds.length})
            </span>
          </button>

          {selectedImageryIds.map((id) => {
            const item = imageryList.find((img) => img.id === id);
            const isActive = activeImageryId === id;
            return (
              <span
                key={id}
                onClick={() => setActiveImageryId(id)}
                className={`inline-flex items-center gap-1 px-1.5 py-0.5 border text-[10px] cursor-pointer transition-all ${
                  isActive
                    ? 'bg-electric-violet/25 border-electric-cyan text-electric-cyan font-bold shadow-sm'
                    : 'bg-space-dark border-electric-violet/40 text-electric-violet hover:border-electric-cyan'
                }`}
                title="Click to display on screen"
              >
                <span>{item ? item.filename : id.substring(0, 8)}</span>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleImagerySelection(id);
                  }}
                  className="hover:text-white ml-1 font-bold"
                  title="Deselect image"
                >
                  ×
                </button>
              </span>
            );
          })}
        </div>

        {/* Action Shortcuts: Run 6 Models + Load SEN12MS-CR */}
        <div className="flex items-center gap-1.5 font-mono">
          <button
            type="button"
            disabled={loadingDataset || isExecuting}
            onClick={handleLoadSen12mscr}
            className="px-2.5 py-1 bg-space-panel hover:bg-space-dark border border-radar-green/50 text-radar-green hover:border-radar-green text-[10px] uppercase font-bold tracking-wider flex items-center gap-1 transition-all disabled:opacity-40"
            title="Download/Stream Sentinel-1 SAR & Sentinel-2 Optical from Hermanni/sen12mscr"
          >
            <Database className="w-3 h-3" />
            <span>{loadingDataset ? 'STREAMING DATASET...' : 'LOAD SEN12MS-CR'}</span>
          </button>

          <button
            type="button"
            disabled={isExecuting}
            onClick={handleRunAll6Models}
            className="px-2.5 py-1 bg-electric-violet/20 hover:bg-electric-violet border border-electric-violet text-electric-cyan hover:text-white text-[10px] uppercase font-bold tracking-wider flex items-center gap-1 transition-all disabled:opacity-40 shadow-brutal-cyan"
            title="Execute segmentation, change detection, captioning, vqa, optical-sar, cloud removal"
          >
            <Sparkles className="w-3 h-3 text-electric-cyan" />
            <span>RUN ALL 6 MODELS</span>
          </button>
        </div>
      </div>

      {/* Popover Imagery Selector */}
      {showImageSelector && (
        <div className="bg-space-dark border border-space-border p-2.5 max-h-40 overflow-y-auto space-y-1.5 font-mono text-xs">
          <div className="text-[10px] text-slate-400 uppercase tracking-wider pb-1 border-b border-space-border">
            SELECT RASTERS FOR INFERENCE (T1 / T2):
          </div>
          {imageryList.length === 0 ? (
            <div className="text-slate-400 py-2 text-center text-[11px]">
              No uploaded imagery found. Upload GeoTIFFs from the SATELLITES tab.
            </div>
          ) : (
            imageryList.map((img) => {
              const isSelected = selectedImageryIds.includes(img.id);
              return (
                <div
                  key={img.id}
                  onClick={() => toggleImagerySelection(img.id)}
                  className={`flex items-center justify-between p-1.5 border cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-electric-violet/20 border-electric-violet text-white'
                      : 'bg-space-panel/60 border-space-border hover:border-slate-500 text-slate-300'
                  }`}
                >
                  <div className="truncate text-[11px] font-semibold">
                    {img.filename}
                    <span className="text-[9px] text-slate-400 ml-2 font-normal">
                      // {img.sensor || 'Raster'}
                    </span>
                  </div>
                  <span className="text-[10px] uppercase">
                    {isSelected ? '[ SELECTED ]' : '[ ATTACH ]'}
                  </span>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Main Command Input Bar */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isExecuting}
            placeholder="Ask Earth something... e.g. 'Where did urban expansion occur between 2022 and 2025?'"
            className="w-full bg-space-black border border-space-border focus:border-electric-cyan px-3.5 py-2.5 text-sm font-mono text-slate-100 placeholder:text-slate-400 outline-none transition-colors"
          />
        </div>
        <BrutalistButton
          type="submit"
          variant="cyan"
          disabled={isExecuting || !prompt.trim()}
          icon={<Send className="w-3.5 h-3.5" />}
        >
          {isExecuting ? 'ANALYZING...' : 'RUN'}
        </BrutalistButton>
      </form>
    </div>
  );
};
