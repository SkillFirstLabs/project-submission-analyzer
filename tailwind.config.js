/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f0ff',
          100: '#e4e4ff',
          200: '#cdcdff',
          300: '#a7a6ff',
          400: '#7a76fa',
          500: '#5c4fe5', // Primary brand color
          600: '#4c3ee0',
          700: '#3e31cb',
          800: '#3226a6',
          900: '#2c2285',
          950: '#1a1457',
        },
        dark: {
          950: '#07080d', // Deep background
          900: '#0b0d19', // Main panels/containers
          800: '#12162b', // Card panels
          700: '#1b203e', // Active elements / hover
          600: '#272d54', // Border outlines
          500: '#3c4475',
          400: '#64748b', // Muted text
          300: '#94a3b8', // Secondary text
          200: '#cbd5e1',
          100: '#f8fafc', // Primary light text
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
