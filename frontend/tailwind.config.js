/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          50: "#1a1a2e",
          100: "#16213e",
          200: "#0f1923",
          300: "#0d1b2a",
          400: "#1b2838",
          500: "#2a3f54",
        },
        gold: {
          400: "#ffd700",
          500: "#f5c518",
          600: "#e6a817",
        },
      },
    },
  },
  plugins: [],
}

