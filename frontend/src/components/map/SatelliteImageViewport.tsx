import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useOrbitStore } from '../../store/useOrbitStore';
import { getImageryPreviewUrl, uploadImagery } from '../../api/imageryApi';
import { loadDatasetSample } from '../../api/datasetApi';
import { EarthMap } from './EarthMap';
import { SatelliteImageChooserModal } from './SatelliteImageChooserModal';
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  SplitSquareVertical,
  Layers,
  Crosshair,
  Image as ImageIcon,
  Globe,
  Upload,
  Database,
  Sliders,
  CheckCircle2,
  Maximize2,
  Satellite,
  ChevronDown
} from 'lucide-react';

export const SatelliteImageViewport: React.FC = () => {
  const {
    imageryList,
    selectedImageryIds,
    activeImageryId,
    setActiveImageryId,
    chooseImage,
    choosePairForComparison,
    setSelectedImageryIds,
    toggleImagerySelection,
    fetchImagery,
    currentResult,
    addMessage,
  } = useOrbitStore();

  // View mode: 'image' or 'globe'
  const [viewMode, setViewMode] = useState<'image' | 'globe'>('image');

  // Chooser Modal & Filmstrip states
  const [isChooserOpen, setIsChooserOpen] = useState(false);
  const [isFilmstripOpen, setIsFilmstripOpen] = useState(true);

  // Split Comparison Slider state
  const [isSplitMode, setIsSplitMode] = useState(false);
  const [splitPos, setSplitPos] = useState(50);
  const [isDraggingSplit, setIsDraggingSplit] = useState(false);

  // Zoom & Pan
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Filters & Overlays
  const [showOverlay, setShowOverlay] = useState(true);
  const [contrastBoost, setContrastBoost] = useState(false);
  const [cursorPos, setCursorPos] = useState<{ x: number; y: number; pctX: number; pctY: number } | null>(null);

  // Upload & Loading states
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingBenchmark, setIsLoadingBenchmark] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  const imageContainerRef = useRef<HTMLDivElement>(null);

  // Resolve chosen images from state
  const chosenImages = selectedImageryIds
    .map((id) => imageryList.find((img) => img.id === id))
    .filter(Boolean) as typeof imageryList;

  // Active chosen image (default to first chosen)
  const activeImage =
    imageryList.find((img) => img.id === activeImageryId) ||
    chosenImages[0] ||
    (imageryList.length > 0 ? imageryList[0] : null);

  // Comparison second image
  const compareImage =
    chosenImages.find((img) => img.id !== activeImage?.id) ||
    (imageryList.length > 1 ? imageryList.find((img) => img.id !== activeImage?.id) : null);

  // Auto-set active imagery ID if missing
  useEffect(() => {
    if (!activeImageryId && activeImage) {
      setActiveImageryId(activeImage.id);
    }
  }, [activeImageryId, activeImage, setActiveImageryId]);

  // Zoom controls
  const handleZoomIn = () => setZoom((z) => Math.min(z * 1.25, 8));
  const handleZoomOut = () => setZoom((z) => Math.max(z / 1.25, 0.4));
  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // Pan interaction
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    setIsPanning(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isPanning) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }

    if (imageContainerRef.current) {
      const rect = imageContainerRef.current.getBoundingClientRect();
      const x = Math.round(e.clientX - rect.left);
      const y = Math.round(e.clientY - rect.top);
      const pctX = Math.max(0, Math.min(100, Math.round((x / rect.width) * 100)));
      const pctY = Math.max(0, Math.min(100, Math.round((y / rect.height) * 100)));

      const naturalW = activeImage?.width || 256;
      const naturalH = activeImage?.height || 256;
      const pixelX = Math.round((pctX / 100) * naturalW);
      const pixelY = Math.round((pctY / 100) * naturalH);

      setCursorPos({ x: pixelX, y: pixelY, pctX, pctY });
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  // Split slider drag handling
  const handleSplitDown = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDraggingSplit(true);
  };

  useEffect(() => {
    const handleGlobalMove = (e: MouseEvent) => {
      if (!isDraggingSplit || !viewportRef.current) return;
      const rect = viewportRef.current.getBoundingClientRect();
      const pos = Math.max(5, Math.min(95, ((e.clientX - rect.left) / rect.width) * 100));
      setSplitPos(pos);
    };

    const handleGlobalUp = () => {
      setIsDraggingSplit(false);
    };

    if (isDraggingSplit) {
      window.addEventListener('mousemove', handleGlobalMove);
      window.addEventListener('mouseup', handleGlobalUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleGlobalMove);
      window.removeEventListener('mouseup', handleGlobalUp);
    };
  }, [isDraggingSplit]);

  // Load SEN12MS-CR benchmark sample
  const handleLoadBenchmark = async () => {
    try {
      setIsLoadingBenchmark(true);
      const res = await loadDatasetSample(0);
      await fetchImagery();
      if (res.imagery_ids && res.imagery_ids.length > 0) {
        chooseImage(res.imagery_ids[0]);
        if (res.imagery_ids.length > 1) {
          setSelectedImageryIds(res.imagery_ids.slice(0, 2));
        }
      }
      addMessage({
        id: `bench_${Date.now()}`,
        role: 'assistant',
        content: `🛰️ Loaded Hermanni/sen12mscr Benchmark Sample #0. Active imagery rendered on viewport.`,
        timestamp: new Date().toLocaleTimeString(),
      });
    } catch (err: any) {
      console.error('Failed to load benchmark:', err);
    } finally {
      setIsLoadingBenchmark(false);
    }
  };

  // File upload trigger
  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setIsUploading(true);
      const res = await uploadImagery(file, 'Sentinel-2');
      await fetchImagery();
      chooseImage(res.id);
    } catch (err: any) {
      console.error('Upload error:', err);
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  // Handle selection for split comparison from modal
  const handleSelectForCompare = (img: typeof imageryList[0]) => {
    if (activeImage) {
      choosePairForComparison(activeImage.id, img.id);
      setIsSplitMode(true);
    } else {
      chooseImage(img.id);
    }
  };

  // If user explicitly toggled to Globe view
  if (viewMode === 'globe') {
    return (
      <div className="relative w-full h-full">
        <EarthMap />
        <button
          onClick={() => setViewMode('image')}
          className="absolute top-3 left-3 z-20 flex items-center gap-1.5 px-3 py-1.5 bg-space-dark/95 border border-electric-cyan text-electric-cyan font-mono text-xs font-bold hover:bg-electric-cyan hover:text-space-black transition-all shadow-brutal"
        >
          <ImageIcon className="w-3.5 h-3.5" />
          <span>SWITCH TO CHOSEN IMAGE VIEW</span>
        </button>
      </div>
    );
  }

  // Active image preview URL
  const activePreviewUrl = activeImage ? getImageryPreviewUrl(activeImage.id) : null;
  const comparePreviewUrl = compareImage ? getImageryPreviewUrl(compareImage.id) : null;

  return (
    <div
      ref={viewportRef}
      className="relative w-full h-full min-h-[400px] border border-space-border bg-[#030306] overflow-hidden select-none flex flex-col"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".tif,.tiff,.png,.jpg,.jpeg"
        onChange={handleFileSelected}
        className="hidden"
      />

      {/* Satellite Image Chooser Modal */}
      <SatelliteImageChooserModal
        isOpen={isChooserOpen}
        onClose={() => setIsChooserOpen(false)}
        onSelectForCompare={handleSelectForCompare}
      />

      {/* Top Header Bar: Choose Imagery Button, Tabs & View Controls */}
      <div className="z-20 bg-space-dark/90 border-b border-space-border px-3 py-1.5 flex items-center justify-between gap-2 flex-wrap font-mono text-xs backdrop-blur-md">
        {/* Left: Choose Image CTA + Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
          {/* Primary Action Button: CHOOSE SATELLITE IMAGE */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsChooserOpen(true);
            }}
            className="px-2.5 py-1 bg-electric-cyan hover:bg-white text-space-black font-bold text-[11px] uppercase flex items-center gap-1.5 shadow-brutal-cyan transition-all shrink-0"
            title="Browse and choose from all available satellite imagery"
          >
            <Satellite className="w-3.5 h-3.5" />
            <span>CHOOSE IMAGE ({imageryList.length})</span>
          </button>

          {/* Dropdown Quick Selector */}
          {imageryList.length > 0 && (
            <div className="relative flex items-center shrink-0">
              <select
                value={activeImage?.id || ''}
                onChange={(e) => {
                  if (e.target.value) {
                    chooseImage(e.target.value);
                  }
                }}
                className="bg-space-panel/90 border border-space-border hover:border-slate-400 text-slate-200 text-[11px] px-2 py-1 pr-6 outline-none focus:border-electric-cyan font-mono cursor-pointer transition-colors max-w-[170px] truncate"
                title="Select satellite image to show on screen"
              >
                {imageryList.map((img) => (
                  <option key={img.id} value={img.id}>
                    {img.filename}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3 h-3 text-slate-400 absolute right-1.5 pointer-events-none" />
            </div>
          )}

          {/* Staged Image Quick Tabs */}
          <div className="hidden xl:flex items-center gap-1.5">
            {chosenImages.map((img, idx) => {
              const isActive = activeImage?.id === img.id;
              return (
                <button
                  key={img.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    chooseImage(img.id);
                  }}
                  className={`px-2 py-0.5 text-[10px] border transition-all flex items-center gap-1 shrink-0 ${
                    isActive
                      ? 'bg-electric-violet/20 border-electric-cyan text-electric-cyan font-bold shadow-sm'
                      : 'bg-space-panel/40 border-space-border hover:border-slate-500 text-slate-400'
                  }`}
                  title={`${img.filename} (${img.sensor || 'Raster'})`}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-electric-cyan" />
                  <span className="truncate max-w-[110px]">{img.filename}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: Compare Slider, Filmstrip Toggle & Globe View */}
        <div className="flex items-center gap-1.5 shrink-0">
          {imageryList.length >= 2 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsSplitMode(!isSplitMode);
              }}
              className={`px-2.5 py-1 text-[11px] border flex items-center gap-1.5 transition-all ${
                isSplitMode
                  ? 'bg-electric-cyan text-space-black border-electric-cyan font-bold shadow-brutal-cyan'
                  : 'bg-space-panel/80 border-space-border text-slate-300 hover:border-electric-cyan'
              }`}
              title="Toggle bitemporal split slider comparison"
            >
              <SplitSquareVertical className="w-3.5 h-3.5" />
              <span>{isSplitMode ? 'EXIT SPLIT' : 'SPLIT COMPARE'}</span>
            </button>
          )}

          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsFilmstripOpen(!isFilmstripOpen);
            }}
            className={`px-2 py-1 text-[11px] border flex items-center gap-1 transition-colors ${
              isFilmstripOpen
                ? 'bg-space-panel text-electric-cyan border-electric-cyan'
                : 'bg-space-dark text-slate-400 border-space-border hover:text-slate-200'
            }`}
            title="Toggle thumbnail gallery filmstrip"
          >
            <ImageIcon className="w-3 h-3" />
            <span className="hidden sm:inline">GALLERY</span>
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              setViewMode('globe');
            }}
            className="px-2 py-1 text-[11px] bg-space-panel/80 border border-space-border text-slate-400 hover:text-slate-200 hover:border-slate-500 flex items-center gap-1 transition-colors"
            title="View regional Earth globe projection"
          >
            <Globe className="w-3 h-3" />
            <span className="hidden sm:inline">GLOBE</span>
          </button>
        </div>
      </div>

      {/* Main Viewport Content Area */}
      <div className="relative flex-1 flex items-center justify-center overflow-hidden cursor-grab active:cursor-grabbing">
        {/* Subtle grid lines background */}
        <div
          className="absolute inset-0 pointer-events-none opacity-15"
          style={{
            backgroundImage:
              'linear-gradient(to right, #334155 1px, transparent 1px), linear-gradient(to bottom, #334155 1px, transparent 1px)',
            backgroundSize: '32px 32px',
          }}
        />

        {activePreviewUrl ? (
          <div
            ref={imageContainerRef}
            className="relative transition-transform duration-75 ease-out select-none"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              filter: contrastBoost ? 'contrast(135%) brightness(110%)' : 'none',
            }}
          >
            {/* Split Comparison Mode */}
            {isSplitMode && comparePreviewUrl ? (
              <div className="relative overflow-hidden border border-electric-cyan shadow-2xl">
                {/* Secondary compare image (T2 / SAR / Cloud-free) */}
                <img
                  src={comparePreviewUrl}
                  alt={compareImage?.filename || 'Compare Image'}
                  className="max-h-[62vh] max-w-[70vw] object-contain block select-none pointer-events-none"
                  draggable={false}
                />

                {/* Primary active image clipped by slider position */}
                <div
                  className="absolute inset-0 overflow-hidden"
                  style={{ width: `${splitPos}%` }}
                >
                  <img
                    src={activePreviewUrl}
                    alt={activeImage?.filename || 'Primary Image'}
                    className="max-h-[62vh] max-w-[70vw] object-contain block select-none pointer-events-none"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    draggable={false}
                  />
                </div>

                {/* Vertical Divider Bar */}
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-electric-cyan shadow-[0_0_10px_rgba(6,182,212,0.9)] cursor-ew-resize flex items-center justify-center pointer-events-auto z-30"
                  style={{ left: `${splitPos}%` }}
                  onMouseDown={handleSplitDown}
                >
                  <div className="w-6 h-6 bg-space-dark border border-electric-cyan text-electric-cyan flex items-center justify-center font-mono text-[9px] font-bold shadow-brutal select-none">
                    ⇹
                  </div>
                </div>

                {/* Left/Right floating labels */}
                <div className="absolute top-2 left-2 px-1.5 py-0.5 bg-space-dark/90 border border-space-border text-[9px] font-mono text-electric-cyan font-bold pointer-events-none">
                  [PRIMARY] {activeImage?.sensor || activeImage?.filename}
                </div>
                <div className="absolute top-2 right-2 px-1.5 py-0.5 bg-space-dark/90 border border-space-border text-[9px] font-mono text-radar-green font-bold pointer-events-none">
                  [COMPARE] {compareImage?.sensor || compareImage?.filename}
                </div>
              </div>
            ) : (
              /* Single Primary Image View */
              <div className="relative border border-space-border shadow-2xl bg-black">
                <img
                  src={activePreviewUrl}
                  alt={activeImage?.filename || 'Satellite Raster'}
                  className="max-h-[64vh] max-w-[75vw] object-contain block select-none pointer-events-none"
                  draggable={false}
                />

                {/* Vector Analysis Polygons / Mask Overlay */}
                {showOverlay && currentResult?.geojson?.features && (
                  <svg
                    className="absolute inset-0 w-full h-full pointer-events-none"
                    viewBox="0 0 100 100"
                    preserveAspectRatio="none"
                  >
                    <rect
                      x="20"
                      y="20"
                      width="60"
                      height="60"
                      fill="rgba(139, 92, 246, 0.25)"
                      stroke="#06b6d4"
                      strokeWidth="1"
                      strokeDasharray="3 2"
                    />
                  </svg>
                )}
              </div>
            )}
          </div>
        ) : (
          /* Empty State: No image chosen */
          <div className="flex flex-col items-center justify-center text-center p-8 max-w-md space-y-4 font-mono select-none">
            <div className="w-14 h-14 border border-dashed border-electric-cyan/60 flex items-center justify-center text-electric-cyan mb-2 shadow-brutal-cyan">
              <ImageIcon className="w-7 h-7" />
            </div>

            <div className="space-y-1">
              <h3 className="text-base font-bold text-white uppercase tracking-wider">
                CHOOSE SATELLITE IMAGE TO DISPLAY
              </h3>
              <p className="font-sans text-xs text-slate-400 leading-relaxed">
                Select an earth-observation image from the catalog, load the SEN12MS-CR benchmark, or upload your own GeoTIFF raster.
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
              <button
                onClick={() => setIsChooserOpen(true)}
                className="px-3.5 py-2 bg-electric-cyan text-space-black font-bold text-xs uppercase flex items-center gap-1.5 shadow-brutal-cyan hover:bg-white transition-all"
              >
                <Satellite className="w-3.5 h-3.5" />
                <span>CHOOSE SATELLITE IMAGE</span>
              </button>

              <button
                disabled={isLoadingBenchmark}
                onClick={handleLoadBenchmark}
                className="px-3 py-2 bg-space-panel hover:bg-space-dark border border-radar-green/60 text-radar-green text-xs uppercase font-bold flex items-center gap-1.5 transition-all disabled:opacity-50"
              >
                <Database className="w-3.5 h-3.5" />
                <span>{isLoadingBenchmark ? 'STREAMING...' : 'SEN12MS-CR SAMPLE'}</span>
              </button>

              <button
                disabled={isUploading}
                onClick={() => fileInputRef.current?.click()}
                className="px-3 py-2 bg-space-panel hover:bg-space-dark border border-space-border hover:border-slate-400 text-slate-200 text-xs uppercase flex items-center gap-1.5 transition-colors"
              >
                <Upload className="w-3.5 h-3.5 text-electric-cyan" />
                <span>{isUploading ? 'UPLOADING...' : 'UPLOAD GEOTIFF'}</span>
              </button>
            </div>
          </div>
        )}

        {/* Center Target Crosshair Overlay */}
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-30">
          <div className="w-8 h-8 border-t border-b border-electric-cyan" />
          <div className="w-8 h-8 border-l border-r border-electric-cyan -ml-8" />
        </div>
      </div>

      {/* Interactive Bottom Filmstrip / Satellite Image Gallery */}
      {isFilmstripOpen && imageryList.length > 0 && (
        <div className="z-20 bg-space-dark/95 border-t border-space-border px-3 py-2 flex items-center gap-2 overflow-x-auto no-scrollbar font-mono text-xs backdrop-blur-md">
          <div className="text-[10px] text-slate-400 uppercase font-semibold shrink-0">
            CHOOSE IMAGE:
          </div>

          {imageryList.map((img) => {
            const isActive = activeImage?.id === img.id;
            const isStaged = selectedImageryIds.includes(img.id);
            const isSar = (img.sensor || '').toLowerCase().includes('sar');

            return (
              <div
                key={img.id}
                onClick={() => chooseImage(img.id)}
                className={`shrink-0 flex items-center gap-2 p-1.5 border cursor-pointer transition-all ${
                  isActive
                    ? 'bg-electric-violet/20 border-electric-cyan ring-1 ring-electric-cyan shadow-sm text-white'
                    : 'bg-space-panel/60 border-space-border hover:border-slate-400 text-slate-300'
                }`}
                title={`Click to show ${img.filename} on screen`}
              >
                <div className="w-10 h-8 bg-black border border-space-border shrink-0 overflow-hidden flex items-center justify-center">
                  <img
                    src={getImageryPreviewUrl(img.id)}
                    alt={img.filename}
                    className="w-full h-full object-contain pointer-events-none"
                    loading="lazy"
                  />
                </div>
                <div className="text-[10px] leading-tight">
                  <div className="font-bold truncate max-w-[130px]">{img.filename}</div>
                  <div className="text-[9px] text-slate-400 flex items-center gap-1 mt-0.5">
                    <span className={isSar ? 'text-purple-400' : 'text-cyan-400'}>
                      {isSar ? 'SAR' : 'OPTICAL'}
                    </span>
                    {isActive ? (
                      <span className="text-electric-cyan font-bold">• ON SCREEN</span>
                    ) : isStaged ? (
                      <span className="text-slate-400">• STAGED</span>
                    ) : null}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Button to open full chooser modal */}
          <button
            onClick={() => setIsChooserOpen(true)}
            className="shrink-0 px-3 py-2 border border-dashed border-electric-cyan/60 hover:border-electric-cyan text-electric-cyan hover:text-white bg-space-panel/40 text-[10px] font-bold uppercase flex items-center gap-1.5 transition-colors"
          >
            <span>+ BROWSE ALL</span>
          </button>
        </div>
      )}

      {/* Floating Tactical Overlay: Image Metadata Box (Top-Left) */}
      {activeImage && (
        <div className="absolute top-12 left-3 bg-space-dark/95 border border-space-border px-3 py-2 font-mono text-[10px] text-slate-300 pointer-events-none backdrop-blur-md shadow-brutal">
          <div className="flex items-center gap-1.5 text-electric-cyan font-bold">
            <span className="w-2 h-2 bg-electric-cyan animate-pulse rounded-full" />
            <span>CHOSEN SATELLITE IMAGE // ACTIVE VIEWPORT</span>
          </div>
          <div className="text-slate-100 font-semibold mt-1 truncate max-w-[260px]">
            {activeImage.filename}
          </div>
          <div className="text-slate-400 mt-0.5 space-y-0.5">
            <div>
              SENSOR: <span className="text-slate-200">{activeImage.sensor || 'Sentinel-2 (Optical)'}</span>
            </div>
            <div>
              DIMENSIONS: <span className="text-slate-200">{activeImage.width || 256} × {activeImage.height || 256} px</span>
            </div>
            <div>
              CRS: <span className="text-electric-cyan font-bold">{activeImage.crs || 'EPSG:4326'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Floating Tactical Overlay: Real-Time Cursor HUD (Bottom-Left) */}
      {cursorPos && activeImage && (
        <div className="absolute bottom-16 left-3 bg-space-dark/90 border border-space-border px-2.5 py-1.5 font-mono text-[10px] text-slate-400 pointer-events-none backdrop-blur-sm hidden sm:block">
          <div className="flex items-center gap-3">
            <span className="text-electric-cyan font-bold flex items-center gap-1">
              <Crosshair className="w-3 h-3" />
              <span>PIXEL: [{cursorPos.x}, {cursorPos.y}]</span>
            </span>
            <span>REL: {cursorPos.pctX}% X / {cursorPos.pctY}% Y</span>
            <span className="text-radar-green">ZOOM: {Math.round(zoom * 100)}%</span>
          </div>
        </div>
      )}

      {/* Floating Tactical Overlay: Viewport Controls (Bottom-Right) */}
      <div className="absolute bottom-16 right-3 flex items-center gap-1 z-20 font-mono text-xs select-none">
        <div className="bg-space-dark/95 border border-space-border flex items-center p-0.5 shadow-brutal backdrop-blur-md">
          <button
            onClick={handleZoomIn}
            className="p-1.5 hover:bg-space-panel text-slate-200 hover:text-white transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleZoomOut}
            className="p-1.5 hover:bg-space-panel text-slate-200 hover:text-white transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleResetZoom}
            className="p-1.5 hover:bg-space-panel text-slate-200 hover:text-white transition-colors"
            title="Reset Zoom & Pan"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <div className="w-px h-4 bg-space-border mx-0.5" />

          <button
            onClick={() => setContrastBoost(!contrastBoost)}
            className={`p-1.5 transition-colors ${
              contrastBoost ? 'text-electric-cyan bg-electric-cyan/20' : 'text-slate-400 hover:text-white'
            }`}
            title="Toggle High-Contrast Stretch Filter"
          >
            <Sliders className="w-3.5 h-3.5" />
          </button>

          {currentResult?.geojson && (
            <button
              onClick={() => setShowOverlay(!showOverlay)}
              className={`p-1.5 transition-colors ${
                showOverlay ? 'text-electric-violet bg-electric-violet/20' : 'text-slate-500 hover:text-white'
              }`}
              title="Toggle Analysis Vector Overlays"
            >
              <Layers className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
