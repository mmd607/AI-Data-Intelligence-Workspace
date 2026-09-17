/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // Full dark/premium design-token palette is finalized in Phase 07 per
      // 02_DOCS/UI_UX_SPEC.md §2/§9 (open question — exact hex values pending).
      // Phase 01 only needs a workable dark base so the shell isn't unstyled.
      colors: {
        surface: {
          DEFAULT: "#0b0d12",
          raised: "#12151c",
        },
        accent: {
          DEFAULT: "#6ee7ff",
        },
      },
    },
  },
  plugins: [],
};
