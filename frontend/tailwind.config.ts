import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#EEF1F6",
        surface: "#FFFFFF",
        ink: "#171B26",
        "ink-soft": "#4B5468",
        ledger: {
          DEFAULT: "#1F3A5F",
          light: "#2C4F7C",
          dark: "#152943",
        },
        stamp: {
          red: "#B3432B",
          amber: "#D98E2B",
          green: "#3A7D5C",
          slate: "#5B6472",
        },
        hairline: "rgba(23,27,38,0.12)",
      },
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        body: ["var(--font-body)", "sans-serif"],
        mono: ["var(--font-data)", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "12px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(23,27,38,0.06), 0 1px 0 rgba(23,27,38,0.04)",
      },
    },
  },
  plugins: [],
};
export default config;
