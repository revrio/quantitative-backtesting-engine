/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        bg: {
          app: '#06080d',
          surface: '#0c1017',
          elevated: '#111720',
          hover: '#161d28',
        },
        border: {
          subtle: '#1a2232',
          medium: '#243044',
        },
        text: {
          primary: '#e8ecf2',
          secondary: '#8b95a5',
          muted: '#4e5969',
        },
        accent: {
          cyan: '#00d4ff',
          cyanDim: '#0a3d4f',
        },
        status: {
          bullish: '#00e5a0',
          bullishDim: '#0a3d2f',
          bearish: '#ff4757',
          bearishDim: '#3d0a15',
          warning: '#ffb347',
          warningDim: '#3d2a0a',
        },
      },
      fontSize: {
        base: '14px',
      },
    },
  },
  plugins: [],
};
