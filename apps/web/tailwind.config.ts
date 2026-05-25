import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f1720",
        sand: "#efe6da",
        ember: "#d26a2c",
        steel: "#7992a3",
        paper: "#fbf7f1",
      },
      boxShadow: {
        panel: "0 24px 80px rgba(15, 23, 32, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;

