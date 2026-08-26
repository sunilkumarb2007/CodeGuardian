/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#070707',
          900: '#0A0A0A',
          850: '#101010',
          800: '#141414',
          700: '#1C1C1C',
          600: '#262626',
          500: '#3A3A3A',
          400: '#6B6B6B',
          300: '#A3A3A3',
        },
        lime: {
          DEFAULT: '#C6FF3D',
          soft: '#E4FF9B',
          deep: '#8FD400',
        },
        signal: {
          blue: '#5B8CFF',
          orange: '#FF7A3D',
          pink: '#FF4D9D',
          purple: '#A56BFF',
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        card: '28px',
        pill: '999px',
      },
      boxShadow: {
        lift: '0 24px 80px -32px rgba(0,0,0,0.9)',
        glow: '0 0 0 1px rgba(198,255,61,0.35), 0 0 48px -12px rgba(198,255,61,0.45)',
      },
      keyframes: {
        marquee: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
        pulseRing: {
          '0%': { boxShadow: '0 0 0 0 rgba(198,255,61,0.45)' },
          '70%': { boxShadow: '0 0 0 14px rgba(198,255,61,0)' },
          '100%': { boxShadow: '0 0 0 0 rgba(198,255,61,0)' },
        },
        gridDrift: {
          '0%': { backgroundPosition: '0 0' },
          '100%': { backgroundPosition: '80px 80px' },
        },
        logoFloat: {
          '0%, 100%': { transform: 'translateY(0) scale(1)' },
          '50%': { transform: 'translateY(-10px) scale(1.03)' },
        },
        logoPulse: {
          '0%, 100%': { opacity: '0.55', transform: 'scale(0.92)' },
          '50%': { opacity: '1', transform: 'scale(1.06)' },
        },
      },
      animation: {
        marquee: 'marquee 26s linear infinite',
        pulseRing: 'pulseRing 1.8s ease-out infinite',
        gridDrift: 'gridDrift 18s linear infinite',
        logoFloat: 'logoFloat 6s ease-in-out infinite',
        logoPulse: 'logoPulse 1.4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
