/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
        // Paleta dark "Anchieta": navy institucional + amarelo de destaque
        navy: {
          950: '#0a1322',
          900: '#0b1422',
          850: '#0f1a2e',
          800: '#131f36',
          750: '#15223c',
          700: '#15294a',
          600: '#1d2f52',
          line: '#1e2a40',
        },
        accent: {
          DEFAULT: '#facc15',
          ink: '#3a2e00',
        },
      },
      animation: {
        'slide-up': 'slide-up 250ms ease-out',
        'fade-in': 'fade-in 200ms ease-out',
        typing: 'typing 1.2s ease-in-out infinite',
        'flash-green': 'flash-green 4s ease-out',
        'slide-in-right': 'slide-in-right 300ms cubic-bezier(0.16, 1, 0.3, 1)',
      },
      keyframes: {
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        typing: {
          '0%, 60%, 100%': { opacity: '0.3', transform: 'translateY(0)' },
          '30%': { opacity: '1', transform: 'translateY(-3px)' },
        },
        'flash-green': {
          '0%': { backgroundColor: 'rgb(220 252 231)' },
          '60%': { backgroundColor: 'rgb(220 252 231)' },
          '100%': { backgroundColor: 'transparent' },
        },
        'slide-in-right': {
          from: { opacity: '0', transform: 'translateX(20px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
}
