import React from 'react';

export const SubtleGalaxy: React.FC = () => {
  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden select-none">
      {/* Base Light Canvas */}
      <div className="absolute inset-0 bg-[#FAFAFC]" />

      {/* Very subtle celestial gradients (crimson + indigo at 4% opacity) */}
      <div 
        className="absolute -top-[20%] left-1/2 -translate-x-1/2 w-[900px] h-[500px] rounded-full blur-[140px] opacity-[0.045]"
        style={{
          background: 'radial-gradient(circle, #C1122F 0%, #8B5CF6 60%, transparent 100%)',
        }}
      />
      <div 
        className="absolute bottom-0 right-[10%] w-[600px] h-[400px] rounded-full blur-[120px] opacity-[0.035]"
        style={{
          background: 'radial-gradient(circle, #E63946 0%, #3B82F6 70%, transparent 100%)',
        }}
      />

      {/* Delicate static celestial dust speckles */}
      <svg className="absolute inset-0 w-full h-full opacity-[0.2]" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="stardust" width="120" height="120" patternUnits="userSpaceOnUse">
            <circle cx="12" cy="18" r="0.8" fill="#C1122F" opacity="0.6" />
            <circle cx="75" cy="42" r="0.6" fill="#1F2937" opacity="0.4" />
            <circle cx="105" cy="95" r="0.7" fill="#6B7280" opacity="0.5" />
            <circle cx="38" cy="80" r="0.5" fill="#C1122F" opacity="0.5" />
            <circle cx="90" cy="15" r="0.6" fill="#4B5563" opacity="0.3" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#stardust)" />
      </svg>
    </div>
  );
};
