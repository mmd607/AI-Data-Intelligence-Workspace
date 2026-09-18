import defaultTheme from "tailwindcss/defaultTheme";

/**
 * Finalized dark/premium design-token palette — resolves 02_DOCS/UI_UX_SPEC.md §9's
 * "exact color palette"/"exact typography" open questions (Phase 07, ADR-016).
 *
 * - `accent` (cyan, unchanged from Phase 01) is the ONE primary accent — used for the
 *   dataset core, every deterministic/computed domain and feature node, and interactive
 *   states across the 2D chrome.
 * - `accent.secondary` (violet) is the ONE secondary accent, reserved exclusively for
 *   AI-generated/AI-sourced content (the AI Insights node, its panel, and
 *   `panels/AIExplanationBlock.tsx`) — a deliberate, spatial reinforcement of product
 *   principle 2 (computed vs. AI-generated must always be visually distinguishable), not
 *   decoration. It is never used for deterministic data.
 * - Semantic good/warning/critical states reuse Tailwind's own desaturated
 *   emerald/amber/rose scales at low opacity (`components/Badge.tsx`'s existing,
 *   Phase-06-tested pattern) rather than inventing new hexes — already satisfies
 *   §2's "desaturated, low-luminance, never saturated neon" rule.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0a0b0f",
          raised: "#12151c",
          overlay: "rgba(6, 7, 10, 0.72)",
        },
        accent: {
          DEFAULT: "#6ee7ff",
          secondary: "#a78bfa",
        },
      },
      fontFamily: {
        sans: ["Inter", ...defaultTheme.fontFamily.sans],
        mono: ["JetBrains Mono", ...defaultTheme.fontFamily.mono],
      },
    },
  },
  plugins: [],
};
