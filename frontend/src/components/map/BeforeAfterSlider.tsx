import React, { useRef, useState, useEffect } from 'react';
import { useMapStore } from '../../store/useMapStore';

export const BeforeAfterSlider: React.FC = () => {
  const { beforeAfter, setBeforeAfterSlider } = useMapStore();
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handlePointerDown = () => setIsDragging(true);

  useEffect(() => {
    const handlePointerMove = (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
      const pct = Math.round((x / rect.width) * 100);
      setBeforeAfterSlider(pct);
    };

    const handlePointerUp = () => setIsDragging(false);

    if (isDragging) {
      window.addEventListener('mousemove', handlePointerMove);
      window.addEventListener('mouseup', handlePointerUp);
    }

    return () => {
      window.removeEventListener('mousemove', handlePointerMove);
      window.removeEventListener('mouseup', handlePointerUp);
    };
  }, [isDragging, setBeforeAfterSlider]);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 pointer-events-none z-10 overflow-hidden"
    >
      {/* Divider line */}
      <div
        className="absolute top-0 bottom-0 w-0.5 bg-electric-cyan shadow-[0_0_8px_rgba(6,182,212,0.8)] pointer-events-auto cursor-ew-resize flex items-center justify-center"
        style={{ left: `${beforeAfter.sliderPosition}%` }}
        onMouseDown={handlePointerDown}
      >
        <div className="w-8 h-8 bg-space-dark border-2 border-electric-cyan text-electric-cyan flex items-center justify-center font-mono text-[10px] font-bold shadow-brutal select-none">
          ⇹
        </div>
      </div>

      {/* Left label (T1) */}
      <div className="absolute top-4 left-4 bg-space-dark/90 border border-space-border px-2.5 py-1 font-mono text-[10px] font-bold text-slate-300 pointer-events-none">
        {beforeAfter.beforeLabel}
      </div>

      {/* Right label (T2) */}
      <div className="absolute top-4 right-4 bg-space-dark/90 border border-space-border px-2.5 py-1 font-mono text-[10px] font-bold text-electric-cyan pointer-events-none">
        {beforeAfter.afterLabel}
      </div>
    </div>
  );
};
