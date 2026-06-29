/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#eaf2ff",
        muted: "#9cb0c8",
        panel: "#0f1728",
        panel2: "#101c31",
        accent: "#22d3ee",
        warn: "#f59e0b",
        danger: "#ef4444",
        success: "#10b981"
      },
      boxShadow: {
        panel: "0 12px 30px rgba(0, 0, 0, 0.35)",
        glow: "0 0 40px rgba(34, 211, 238, 0.16)"
      },
      keyframes: {
        drift: {
          "0%,100%": { transform: "translate(0,0)" },
          "50%": { transform: "translate(18px, -14px)" }
        },
        rise: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        }
      },
      animation: {
        drift: "drift 24s ease-in-out infinite",
        rise: "rise 420ms cubic-bezier(0.2,0.8,0.2,1) both"
      }
    }
  },
  plugins: []
};
