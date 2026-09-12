import React from 'react';

export const OrbitalLines: React.FC = () => {
  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden opacity-25">
      <svg
        className="w-full h-full"
        viewBox="0 0 1600 1000"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Large Equatorial Orbit */}
        <ellipse
          cx="800"
          cy="500"
          rx="700"
          ry="320"
          stroke="#8b5cf6"
          strokeWidth="1"
          strokeDasharray="6 8"
          className="opacity-40"
        />

        {/* Polar Orbit */}
        <ellipse
          cx="800"
          cy="500"
          rx="340"
          ry="650"
          stroke="#06b6d4"
          strokeWidth="1"
          strokeDasharray="4 6"
          className="opacity-30"
          transform="rotate(25 800 500)"
        />

        {/* Sun-synchronous Orbit (Sentinel constellation path) */}
        <ellipse
          cx="800"
          cy="500"
          rx="520"
          ry="440"
          stroke="#38bdf8"
          strokeWidth="1"
          strokeDasharray="2 10"
          className="opacity-35"
          transform="rotate(-35 800 500)"
        />

        {/* Orbit Node Markers */}
        <circle cx="1500" cy="500" r="3" fill="#8b5cf6" />
        <circle cx="100" cy="500" r="3" fill="#8b5cf6" />
        <circle cx="800" cy="180" r="2.5" fill="#06b6d4" />
      </svg>
    </div>
  );
};
