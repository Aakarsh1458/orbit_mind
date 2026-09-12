import React, { useState, useEffect } from 'react';
import { useOrbitStore } from '../store/useOrbitStore';
import { uploadImagery, listImagery, getImageryPreviewUrl } from '../api/imageryApi';
import { ImageryItem } from '../types/api';
import { BrutalistButton } from '../components/brutalist/BrutalistButton';
import { BrutalistBadge } from '../components/brutalist/BrutalistBadge';
import { Globe, Upload, Satellite, CheckCircle, FileCheck, Layers, RefreshCw, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const CONSTELLATIONS = [
  {
    name: 'SENTINEL-2',
    agency: 'ESA / COPERNICUS',
    modality: 'MULTISPECTRAL OPTICAL',
    bands: '13 BANDS (VNIR + SWIR)',
    revisit: '5 DAYS (CONSTELLATION)',
    status: 'CONNECTED',
    color: 'text-satellite-optical',
  },
  {
    name: 'SENTINEL-1',
    agency: 'ESA / COPERNICUS',
    modality: 'C-BAND SYNTHETIC APERTURE RADAR (SAR)',
    bands: 'VV + VH POLARIZATION',
    revisit: '6 DAYS',
    status: 'CONNECTED',
    color: 'text-satellite-sar',
  },
  {
    name: 'LANDSAT 8 / 9',
    agency: 'NASA / USGS',
    modality: 'OPTICAL + THERMAL INFRARED (TIRS)',
    bands: '11 BANDS',
    revisit: '8 DAYS (OFFSET)',
    status: 'CONNECTED',
    color: 'text-electric-cyan',
  },
];

export const Satellites: React.FC = () => {
  const navigate = useNavigate();
  const { imageryList, fetchImagery, selectedImageryIds, toggleImagerySelection, chooseImage } = useOrbitStore();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [sensorType, setSensorType] = useState('Sentinel-2');

  const handleViewOnScreen = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    chooseImage(id);
    navigate('/workspace');
  };

  useEffect(() => {
    fetchImagery();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const res = await uploadImagery(file, sensorType);
      setUploadSuccess(`Successfully ingested GeoTIFF '${res.filename}' (${res.crs || 'EPSG:4326'})`);
      await fetchImagery();
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleOpenWorkspace = () => {
    navigate('/workspace');
  };

  return (
    <div className="relative z-10 max-w-7xl mx-auto px-4 py-8 space-y-10">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-space-border pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2 font-mono text-xs text-electric-cyan uppercase">
            <Satellite className="w-4 h-4" />
            <span>EARTH OBSERVATION SENSORS & IMAGERY CATALOG</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-mono font-bold text-white uppercase">
            SATELLITE GROUND REPOSITORY
          </h1>
          <p className="font-sans text-slate-300 text-sm max-w-2xl">
            Inspect active earth-observation satellite constellations, ingest georeferenced GeoTIFF rasters, and stage imagery for AI model routing.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <BrutalistButton
            variant="secondary"
            size="sm"
            onClick={() => fetchImagery()}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            REFRESH
          </BrutalistButton>
          <BrutalistButton
            variant="cyan"
            size="sm"
            onClick={handleOpenWorkspace}
            icon={<Layers className="w-3.5 h-3.5" />}
          >
            STAGE IN WORKSPACE ({selectedImageryIds.length})
          </BrutalistButton>
        </div>
      </div>

      {/* Constellation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
        {CONSTELLATIONS.map((c, i) => (
          <div
            key={i}
            className="bg-space-card border border-space-border p-4 space-y-3 shadow-brutal flex flex-col justify-between"
          >
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-400 uppercase">{c.agency}</span>
                <BrutalistBadge variant="green" size="sm" dot>
                  {c.status}
                </BrutalistBadge>
              </div>
              <div className={`text-lg font-bold ${c.color}`}>{c.name}</div>
              <div className="text-[11px] text-slate-300 pt-1 font-sans">{c.modality}</div>
            </div>

            <div className="pt-3 border-t border-space-border space-y-1 text-[10px] text-slate-400">
              <div>BANDS: <span className="text-slate-200">{c.bands}</span></div>
              <div>ORBITAL REVISIT: <span className="text-slate-200">{c.revisit}</span></div>
            </div>
          </div>
        ))}
      </div>

      {/* GeoTIFF Ingestion Dropzone */}
      <div className="bg-space-dark border border-space-border p-6 shadow-brutal space-y-4">
        <div className="flex items-center justify-between border-b border-space-border pb-2 font-mono text-xs">
          <span className="font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
            <Upload className="w-4 h-4 text-electric-cyan" />
            INGEST SATELLITE RASTER (GEOTIFF)
          </span>
          <span className="text-slate-400 text-[10px]">
            EXTRACTS: CRS, BOUNDS, CHANNELS, AFFINE TRANSFORM
          </span>
        </div>

        <div className="flex flex-col md:flex-row items-center gap-4">
          <div className="w-full md:w-48 font-mono text-xs space-y-1">
            <label className="text-slate-400 block text-[10px] uppercase">SENSOR MODALITY:</label>
            <select
              value={sensorType}
              onChange={(e) => setSensorType(e.target.value)}
              className="w-full bg-space-black border border-space-border px-2.5 py-2 text-slate-200 outline-none focus:border-electric-cyan"
            >
              <option value="Sentinel-2">Sentinel-2 (Optical)</option>
              <option value="Sentinel-1">Sentinel-1 (SAR Radar)</option>
              <option value="Landsat-8">Landsat-8 (Optical/Thermal)</option>
              <option value="Custom">Custom Aerial / UAV</option>
            </select>
          </div>

          <div className="flex-1 w-full relative">
            <label
              htmlFor="geotiff-upload"
              className="flex flex-col items-center justify-center border-2 border-dashed border-space-border hover:border-electric-cyan/80 p-6 cursor-pointer bg-space-panel/40 transition-colors group"
            >
              <Upload className="w-6 h-6 text-slate-400 group-hover:text-electric-cyan mb-2" />
              <div className="font-mono text-xs font-bold text-slate-200">
                {isUploading ? 'EXTRACTING GEOSPATIAL METADATA...' : 'SELECT OR DROP GEOTIFF (.TIF, .TIFF)'}
              </div>
              <div className="font-mono text-[10px] text-slate-400 mt-1">
                MAX 500 MB // SUPPORTED: WGS84, UTM, EPSG:4326, EPSG:3857
              </div>
              <input
                id="geotiff-upload"
                type="file"
                accept=".tif,.tiff"
                onChange={handleFileUpload}
                disabled={isUploading}
                className="hidden"
              />
            </label>
          </div>
        </div>

        {uploadSuccess && (
          <div className="p-2.5 bg-radar-green/15 border border-radar-green text-radar-green font-mono text-xs flex items-center gap-2">
            <CheckCircle className="w-4 h-4 shrink-0" />
            <span>{uploadSuccess}</span>
          </div>
        )}

        {uploadError && (
          <div className="p-2.5 bg-radar-red/15 border border-radar-red text-radar-red font-mono text-xs">
            UPLOAD FAILED: {uploadError}
          </div>
        )}
      </div>

      {/* Uploaded Raster Inventory Table */}
      <div className="space-y-3 font-mono text-xs">
        <div className="flex items-center justify-between">
          <span className="font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
            <Layers className="w-4 h-4 text-electric-violet" />
            CONNECTED IMAGERY INVENTORY ({imageryList.length})
          </span>
          <span className="text-[10px] text-slate-400">// CLICK ROW TO STAGE FOR INFERENCE</span>
        </div>

        {imageryList.length === 0 ? (
          <div className="bg-space-dark border border-space-border p-8 text-center text-slate-500 font-mono text-xs">
            No satellite rasters uploaded yet. Upload a GeoTIFF above to begin analysis.
          </div>
        ) : (
          <div className="border border-space-border overflow-x-auto shadow-brutal bg-space-card">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-space-panel/90 border-b border-space-border text-[10px] text-slate-400 uppercase">
                  <th className="p-3">PREVIEW</th>
                  <th className="p-3">STAGE</th>
                  <th className="p-3">FILENAME</th>
                  <th className="p-3">SENSOR</th>
                  <th className="p-3">CRS</th>
                  <th className="p-3">DIMENSIONS</th>
                  <th className="p-3">FILE SIZE</th>
                  <th className="p-3 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-space-border">
                {imageryList.map((img: ImageryItem) => {
                  const isSelected = selectedImageryIds.includes(img.id);
                  const sizeMb = (img.file_size_bytes / (1024 * 1024)).toFixed(2);
                  return (
                    <tr
                      key={img.id}
                      onClick={() => toggleImagerySelection(img.id)}
                      className={`cursor-pointer transition-colors ${
                        isSelected
                          ? 'bg-electric-violet/15 text-white font-bold'
                          : 'hover:bg-space-panel/50 text-slate-300'
                      }`}
                    >
                      <td className="p-3">
                        <div className="w-12 h-9 bg-black border border-space-border overflow-hidden flex items-center justify-center">
                          <img
                            src={getImageryPreviewUrl(img.id)}
                            alt={img.filename}
                            className="w-full h-full object-contain pointer-events-none"
                            loading="lazy"
                          />
                        </div>
                      </td>
                      <td className="p-3">
                        <span
                          className={`inline-block px-1.5 py-0.5 border text-[9px] uppercase ${
                            isSelected
                              ? 'border-electric-violet text-electric-violet bg-space-dark font-bold'
                              : 'border-slate-600 text-slate-500'
                          }`}
                        >
                          {isSelected ? 'STAGED' : 'ADD'}
                        </span>
                      </td>
                      <td className="p-3 font-semibold text-slate-100">{img.filename}</td>
                      <td className="p-3 text-slate-400">{img.sensor || 'Sentinel-2'}</td>
                      <td className="p-3 text-electric-cyan font-bold">{img.crs || 'EPSG:4326'}</td>
                      <td className="p-3 text-slate-400">
                        {img.width && img.height ? `${img.width} × ${img.height} px` : 'N/A'}
                      </td>
                      <td className="p-3 text-slate-400">{sizeMb} MB</td>
                      <td className="p-3 text-right">
                        <button
                          onClick={(e) => handleViewOnScreen(e, img.id)}
                          className="px-2.5 py-1 bg-electric-cyan hover:bg-white text-space-black font-bold uppercase text-[10px] shadow-brutal-cyan inline-flex items-center gap-1 transition-all"
                        >
                          <Eye className="w-3 h-3" />
                          <span>VIEW ON SCREEN</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
