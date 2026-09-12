import React, { useState, useRef } from 'react';
import { useOrbitStore } from '../../store/useOrbitStore';
import { getImageryPreviewUrl, uploadImagery } from '../../api/imageryApi';
import { loadDatasetSample } from '../../api/datasetApi';
import { ImageryItem } from '../../types/api';
import {
  X,
  CheckCircle2,
  Image as ImageIcon,
  Upload,
  Database,
  SplitSquareVertical,
  Layers,
  Search,
  Check,
  Eye,
  Satellite
} from 'lucide-react';

interface SatelliteImageChooserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectForCompare?: (img: ImageryItem) => void;
}

export const SatelliteImageChooserModal: React.FC<SatelliteImageChooserModalProps> = ({
  isOpen,
  onClose,
  onSelectForCompare,
}) => {
  const {
    imageryList,
    selectedImageryIds,
    activeImageryId,
    chooseImage,
    toggleImagerySelection,
    fetchImagery,
  } = useOrbitStore();

  const [filter, setFilter] = useState<'all' | 'optical' | 'sar' | 'staged'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isLoadingBenchmark, setIsLoadingBenchmark] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  // Filter items
  const filteredList = imageryList.filter((img) => {
    const s = (img.sensor || '').toLowerCase();
    const fn = img.filename.toLowerCase();
    const q = searchQuery.toLowerCase();

    const matchesSearch = fn.includes(q) || s.includes(q);
    if (!matchesSearch) return false;

    if (filter === 'optical') return s.includes('optical') || s.includes('sentinel-2') || s.includes('landsat') || fn.includes('optical');
    if (filter === 'sar') return s.includes('sar') || s.includes('radar') || s.includes('sentinel-1') || fn.includes('sar');
    if (filter === 'staged') return selectedImageryIds.includes(img.id);
    return true;
  });

  const handleChooseAndDisplay = (img: ImageryItem) => {
    chooseImage(img.id);
    onClose();
  };

  const handleCompare = (img: ImageryItem) => {
    if (onSelectForCompare) {
      onSelectForCompare(img);
    }
    onClose();
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);

    try {
      const res = await uploadImagery(file, 'Sentinel-2');
      await fetchImagery();
      chooseImage(res.id);
      onClose();
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleLoadBenchmark = async () => {
    try {
      setIsLoadingBenchmark(true);
      const res = await loadDatasetSample(0);
      await fetchImagery();
      if (res.imagery_ids && res.imagery_ids.length > 0) {
        chooseImage(res.imagery_ids[0]);
      }
      onClose();
    } catch (err: any) {
      console.error('Failed to load benchmark:', err);
    } finally {
      setIsLoadingBenchmark(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm select-none font-mono">
      {/* Hidden file upload input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".tif,.tiff,.png,.jpg,.jpeg"
        onChange={handleFileUpload}
        className="hidden"
      />

      <div className="relative w-full max-w-4xl max-h-[90vh] bg-space-card border-2 border-electric-cyan flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Top Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-space-border bg-space-dark">
          <div className="flex items-center gap-2">
            <Satellite className="w-4 h-4 text-electric-cyan" />
            <span className="text-xs font-bold uppercase tracking-wider text-white">
              CHOOSE SATELLITE IMAGE TO DISPLAY ON SCREEN
            </span>
            <span className="text-[10px] text-slate-400 hidden sm:inline">
              // {imageryList.length} IMAGES AVAILABLE
            </span>
          </div>

          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white hover:bg-space-panel border border-transparent hover:border-space-border transition-colors"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Filter & Action Controls Bar */}
        <div className="p-3 border-b border-space-border bg-space-panel/60 flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {[
              { id: 'all', label: 'ALL SENSORS' },
              { id: 'optical', label: 'OPTICAL (S2/LANDSAT)' },
              { id: 'sar', label: 'RADAR (S1 SAR)' },
              { id: 'staged', label: `STAGED (${selectedImageryIds.length})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setFilter(tab.id as any)}
                className={`px-2.5 py-1 text-[11px] border transition-colors ${
                  filter === tab.id
                    ? 'bg-electric-cyan text-space-black border-electric-cyan font-bold shadow-sm'
                    : 'bg-space-dark border-space-border text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Quick Actions: Load Benchmark & Upload */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleLoadBenchmark}
              disabled={isLoadingBenchmark}
              className="px-2.5 py-1 bg-space-dark hover:bg-space-panel border border-radar-green/60 text-radar-green text-[10px] uppercase font-bold flex items-center gap-1.5 transition-colors disabled:opacity-50"
              title="Load SEN12MS-CR benchmark sample"
            >
              <Database className="w-3 h-3" />
              <span>{isLoadingBenchmark ? 'LOADING...' : 'SEN12MS-CR SAMPLE'}</span>
            </button>

            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="px-2.5 py-1 bg-space-dark hover:bg-space-panel border border-electric-violet/60 text-electric-violet text-[10px] uppercase font-bold flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <Upload className="w-3 h-3" />
              <span>{isUploading ? 'UPLOADING...' : 'UPLOAD GEOTIFF'}</span>
            </button>
          </div>
        </div>

        {/* Search Filter Bar */}
        <div className="px-3 py-2 border-b border-space-border bg-space-dark/80 flex items-center gap-2">
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search satellite imagery by filename or sensor modality..."
            className="w-full bg-transparent border-none outline-none text-xs text-slate-200 placeholder:text-slate-500 font-mono"
          />
        </div>

        {uploadError && (
          <div className="p-2 bg-radar-red/15 border-b border-radar-red text-radar-red text-xs">
            UPLOAD ERROR: {uploadError}
          </div>
        )}

        {/* Satellite Images Cards Grid */}
        <div className="flex-1 overflow-y-auto p-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {filteredList.length === 0 ? (
            <div className="col-span-full py-12 text-center text-slate-500 space-y-3">
              <ImageIcon className="w-10 h-10 mx-auto text-slate-600" />
              <div className="text-xs uppercase font-bold text-slate-400">
                NO MATCHING SATELLITE IMAGES FOUND
              </div>
              <p className="text-[11px] font-sans text-slate-400 max-w-sm mx-auto">
                Upload a GeoTIFF raster above or click 'SEN12MS-CR SAMPLE' to load multi-modal Sentinel-1 & Sentinel-2 benchmark imagery.
              </p>
            </div>
          ) : (
            filteredList.map((img) => {
              const isActive = activeImageryId === img.id;
              const isStaged = selectedImageryIds.includes(img.id);
              const previewUrl = getImageryPreviewUrl(img.id);
              const isSar = (img.sensor || '').toLowerCase().includes('sar');

              return (
                <div
                  key={img.id}
                  className={`bg-space-dark border p-2.5 flex flex-col justify-between transition-all group ${
                    isActive
                      ? 'border-electric-cyan shadow-[0_0_12px_rgba(6,182,212,0.35)] ring-1 ring-electric-cyan'
                      : 'border-space-border hover:border-slate-500'
                  }`}
                >
                  {/* Card Thumbnail Image */}
                  <div
                    onClick={() => handleChooseAndDisplay(img)}
                    className="relative w-full aspect-video bg-black border border-space-border overflow-hidden cursor-pointer group-hover:border-electric-cyan/70 transition-colors flex items-center justify-center"
                  >
                    <img
                      src={previewUrl}
                      alt={img.filename}
                      className="w-full h-full object-contain select-none pointer-events-none"
                      loading="lazy"
                    />

                    {/* Status Badges Overlay */}
                    <div className="absolute top-1.5 left-1.5 flex flex-col gap-1">
                      {isActive && (
                        <span className="px-1.5 py-0.5 bg-electric-cyan text-space-black text-[9px] font-bold uppercase flex items-center gap-1 shadow-sm">
                          <span className="w-1.5 h-1.5 bg-space-black rounded-full animate-pulse" />
                          ACTIVE ON SCREEN
                        </span>
                      )}
                      {isStaged && !isActive && (
                        <span className="px-1.5 py-0.5 bg-electric-violet/80 text-white text-[9px] font-bold uppercase shadow-sm">
                          STAGED FOR AI
                        </span>
                      )}
                    </div>

                    <div className="absolute top-1.5 right-1.5">
                      <span
                        className={`px-1.5 py-0.5 text-[9px] font-bold uppercase border ${
                          isSar
                            ? 'border-purple-500 bg-purple-950/80 text-purple-300'
                            : 'border-cyan-500 bg-cyan-950/80 text-cyan-300'
                        }`}
                      >
                        {isSar ? 'SAR RADAR' : 'OPTICAL'}
                      </span>
                    </div>

                    {/* Hover Click to View Hint */}
                    <div className="absolute inset-0 bg-electric-cyan/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center pointer-events-none">
                      <span className="px-2 py-1 bg-space-dark/95 border border-electric-cyan text-electric-cyan text-[10px] font-bold">
                        CLICK TO VIEW
                      </span>
                    </div>
                  </div>

                  {/* Card Details */}
                  <div className="pt-2 space-y-1">
                    <div className="font-bold text-xs text-white truncate" title={img.filename}>
                      {img.filename}
                    </div>

                    <div className="text-[10px] text-slate-400 flex items-center justify-between">
                      <span>{img.sensor || 'Sentinel-2'}</span>
                      <span className="text-electric-cyan font-mono font-semibold">
                        {img.width && img.height ? `${img.width}×${img.height} px` : 'EPSG:4326'}
                      </span>
                    </div>

                    <div className="text-[9px] text-slate-400 truncate">
                      CRS: {img.crs || 'EPSG:4326'} // {(img.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                    </div>
                  </div>

                  {/* Card Action Buttons */}
                  <div className="pt-2.5 mt-2 border-t border-space-border flex items-center gap-1.5">
                    <button
                      onClick={() => handleChooseAndDisplay(img)}
                      className={`flex-1 py-1.5 text-[10px] uppercase font-bold flex items-center justify-center gap-1 transition-all ${
                        isActive
                          ? 'bg-electric-cyan/20 border border-electric-cyan text-electric-cyan'
                          : 'bg-electric-cyan text-space-black hover:bg-white shadow-brutal-cyan'
                      }`}
                    >
                      <Eye className="w-3 h-3" />
                      <span>{isActive ? 'CURRENT SCREEN' : 'CHOOSE & SHOW'}</span>
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleImagerySelection(img.id);
                      }}
                      className={`px-2 py-1.5 text-[10px] border transition-colors ${
                        isStaged
                          ? 'border-electric-violet text-electric-violet bg-electric-violet/10 font-bold'
                          : 'border-space-border text-slate-400 hover:border-slate-400'
                      }`}
                      title={isStaged ? 'Remove from AI staging' : 'Stage for AI analysis'}
                    >
                      {isStaged ? <Check className="w-3 h-3" /> : '+ AI'}
                    </button>

                    {onSelectForCompare && !isActive && (
                      <button
                        onClick={() => handleCompare(img)}
                        className="px-2 py-1.5 text-[10px] border border-space-border hover:border-electric-cyan text-slate-300 hover:text-white"
                        title="Compare with current image in split view"
                      >
                        <SplitSquareVertical className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-4 py-2.5 border-t border-space-border bg-space-dark flex items-center justify-between text-[11px] text-slate-400">
          <div>
            Click any satellite image card to display it directly on the screen viewport.
          </div>
          <button
            onClick={onClose}
            className="px-3 py-1 bg-space-panel hover:bg-space-card border border-space-border text-slate-200 text-xs uppercase"
          >
            CLOSE
          </button>
        </div>
      </div>
    </div>
  );
};
