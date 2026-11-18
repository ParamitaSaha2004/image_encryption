/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        hice: {
          dark: '#0a0f1d',
          navy: '#0f172a',
          card: '#1e293b',
          border: '#334155',
          accent: '#38bdf8',
          accentGlow: '#0284c7',
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444'
        }
      }
    },
  },
  plugins: [],
}
