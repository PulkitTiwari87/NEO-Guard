/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Design system: aerospace command-console theme, tokens derived from the
        // Stitch "NEO-Guard Planetary Defense Command Dashboard" reference (Phase 3.5).
        canvas: '#101319',
        surface: {
          DEFAULT: '#0b0e13',
          raised: '#191c21',
          overlay: '#1d2025',
          high: '#272a30',
          highest: '#32353b',
        },
        border: {
          DEFAULT: 'rgba(58,73,75,0.4)',
          subtle: 'rgba(58,73,75,0.22)',
          strong: 'rgba(132,148,149,0.55)',
        },
        accent: {
          DEFAULT: '#00f2ff',
          hover: '#5df6ff',
          dim: 'rgba(0,242,255,0.12)',
        },
        secondary: {
          DEFAULT: '#cfbdff',
          hover: '#ded1ff',
          dim: 'rgba(207,189,255,0.12)',
        },
        hazard: {
          DEFAULT: '#ffb86f',
          dim: 'rgba(255,184,111,0.14)',
        },
        safe: {
          DEFAULT: '#7dd8de',
          dim: 'rgba(125,216,222,0.12)',
        },
        muted: {
          DEFAULT: '#849495',
          subtle: '#5c6667',
        },
      },
      fontFamily: {
        sans: ['Geist', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
        heading: ['Space Grotesk', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'display': ['2.5rem', { lineHeight: '1.1', letterSpacing: '-0.03em', fontWeight: '700' }],
        'heading': ['1.5rem', { lineHeight: '1.2', letterSpacing: '-0.02em', fontWeight: '600' }],
        'subheading': ['1.125rem', { lineHeight: '1.4', letterSpacing: '-0.01em', fontWeight: '600' }],
        'body': ['0.9375rem', { lineHeight: '1.6' }],
        'caption': ['0.8125rem', { lineHeight: '1.5' }],
        'label': ['0.75rem', { lineHeight: '1.4', letterSpacing: '0.04em', fontWeight: '500' }],
        'mono-data': ['0.875rem', { lineHeight: '1.5', fontFamily: 'JetBrains Mono, ui-monospace, monospace' }],
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.06)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.1)',
        'glow': '0 0 20px rgba(0,242,255,0.25)',
        'glow-amber': '0 0 16px rgba(255,184,111,0.35)',
      },
      borderRadius: {
        'card': '0.25rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.25s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'radar-sweep': 'radarSweep 6s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        radarSweep: {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' },
        },
      },
    },
  },
  plugins: [],
}
