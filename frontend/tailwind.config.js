/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Barlow"', '"Segoe UI"', "sans-serif"],
        display: ['"Sora"', '"Segoe UI"', "sans-serif"]
      },
      colors: {
        base: {
          50: "#f7f8fb",
          100: "#edf0f5",
          600: "#3a4a66",
          700: "#27364f"
        }
      }
    }
  },
  plugins: []
};

