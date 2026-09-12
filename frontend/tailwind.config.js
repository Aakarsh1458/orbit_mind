/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Deep Cosmos Minimal Visual Identity
        'space-black': '#050508',
        'space-dark': '#0a0612',
        'space-panel': '#0f0a1c',
        'space-card': '#0f0a1c',
        'space-border': 'rgba(168, 85, 247, 0.15)',
        'electric-violet': '#a855f7',
        'electric-purple': '#9333ea',
        'electric-cyan': '#06b6d4',
        'radar-green': '#10b981',
        'radar-amber': '#f59e0b',
        'radar-red': '#ef4444',
        starlight: {
          DEFAULT: '#f8fafc',
          muted: '#94a3b8',
        },
        // Translucent glass surfaces
        glass: {
          DEFAULT: 'rgba(15, 10, 28, 0.72)',
          dark: 'rgba(10, 6, 18, 0.85)',
          light: 'rgba(15, 10, 28, 0.55)',
          border: 'rgba(168, 85, 247, 0.15)',
          highlight: 'rgba(168, 85, 247, 0.12)',
        },
      },
      fontFamily: {
        sans: ['"Helvetica Neue"', 'Helvetica', 'Arial', 'system-ui', 'sans-serif'],
        display: ['"Helvetica Neue"', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'brutal': '2px 2px 0px 0px rgba(168, 85, 247, 0.25)',
        'brutal-cyan': '2px 2px 0px 0px rgba(6, 182, 212, 0.4)',
        'brutal-violet': '2px 2px 0px 0px rgba(168, 85, 247, 0.4)',
        'cosmos': '0 8px 32px 0 rgba(0, 0, 0, 0.6)',
      },
      animation: {
        'pulse-subtle': 'pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        }
      }
    },
  },
  plugins: [],
}
