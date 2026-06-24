import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#2f6f4e",
          dark: "#234f39",
          light: "#e7f1eb",
        },
      },
      fontFamily: {
        sans: ["Heebo", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
