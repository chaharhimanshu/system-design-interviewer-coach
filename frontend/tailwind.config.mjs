/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Futuristic color palette
        'space': {
          50: '#f0f4f8',
          100: '#d9e5f0',
          200: '#b3cde0',
          300: '#8bb3d1',
          400: '#6399c2',
          500: '#3b7fb3',
          600: '#2f659f',
          700: '#1a2332',
          800: '#141a26',
          900: '#0f1419',
        },
        'cyber': {
          50: '#e6ffff',
          100: '#b3ffff',
          200: '#80ffff',
          300: '#4dffff',
          400: '#1affff',
          500: '#00d4ff',
          600: '#00a8cc',
          700: '#007d99',
          800: '#005166',
          900: '#002633',
        },
        'neon': {
          50: '#f0ffff',
          100: '#ccffff',
          200: '#99ffff',
          300: '#66ffff',
          400: '#33ffff',
          500: '#00ffff',
          600: '#00cccc',
          700: '#009999',
          800: '#006666',
          900: '#003333',
        },
        'electric': {
          50: '#f3f0ff',
          100: '#e9e5ff',
          200: '#d4cfff',
          300: '#beb5ff',
          400: '#a99eff',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
        }
      },
      fontFamily: {
        'cyber': ['Inter', 'system-ui', 'sans-serif'],
        'mono': ['Fira Code', 'Monaco', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 3s infinite',
        'float': 'float 3s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'scan': 'scan 2s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' }
        },
        glow: {
          '0%': { boxShadow: '0 0 5px #00d4ff, 0 0 10px #00d4ff, 0 0 15px #00d4ff' },
          '100%': { boxShadow: '0 0 10px #00d4ff, 0 0 20px #00d4ff, 0 0 30px #00d4ff' }
        },
        scan: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' }
        }
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'cyber': '0 0 20px rgba(0, 212, 255, 0.3)',
        'neon': '0 0 20px rgba(100, 255, 218, 0.4)',
        'electric': '0 0 20px rgba(139, 92, 246, 0.3)',
      }
    },
  },
  plugins: [
    // Remove the plugins for now since we're using the new @tailwindcss/postcss
    // require('@tailwindcss/forms'),
    // require('@tailwindcss/typography'),
  ],
}
