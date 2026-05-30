/** @type {import('tailwindcss').Config} */
export default {
  content: ['./app/static/**/*.html', './app/static/js/**/*.js'],
  theme: {
    extend: {
      colors: {
        gold: { 400: '#D4AF37', 500: '#B8960C', 600: '#9A7D0A' },
        navy: { 900: '#0A0E1A', 800: '#0F1629', 700: '#1A2340' },
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      animation: {
        'slide-down': 'slideDown 0.3s ease-out',
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.6s ease-out',
      },
      keyframes: {
        slideDown: { '0%': { transform: 'translateY(-10px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { transform: 'translateY(20px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
      },
    },
  },
  plugins: [],
}
