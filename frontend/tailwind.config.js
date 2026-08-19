/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        asta: {
          void: "#0A0E14",
          panel: "#121821",
          panelAlt: "#171F2B",
          white: "#ECEFF2",
          whiteDim: "#9BA6B4",
          blueDeep: "#14448C",
          blueBright: "#2F7BD4",
          red: "#D0202B",
          yellow: "#F2C230",
          line: "#3C4859",
        },
      },
      fontFamily: {
        display: ["Orbitron", "sans-serif"],
        body: ["Titillium Web", "sans-serif"],
        mono: ["Share Tech Mono", "monospace"],
      },
      keyframes: {
        "pulse-dot": {
          "0%, 100%": { opacity: 1 },
          "50%": { opacity: 0.35 },
        },
        scan: {
          "0%": { top: "8%" },
          "50%": { top: "88%" },
          "100%": { top: "8%" },
        },
        blink: {
          "50%": { opacity: 0 },
        },
      },
      animation: {
        "pulse-dot": "pulse-dot 1.8s ease-in-out infinite",
        scan: "scan 3.2s ease-in-out infinite",
        blink: "blink 1s step-end infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
