/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.{html,js}",
    "./static/**/*.{html,js}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'inter': ['Inter', 'sans-serif'],
        'poppins': ['Poppins', 'sans-serif'],
      },
      colors: {
        'viamigo-purple': {
          light: '#a78bfa',
          DEFAULT: '#8b5cf6',
          dark: '#7c3aed'
        }
      }
    },
  },
  plugins: [],
}