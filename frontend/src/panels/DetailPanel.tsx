import { AnimatePresence, motion } from "framer-motion";
import type { ReactNode } from "react";

/**
 * The shared slide-in inspector shell (`02_DOCS/UI_UX_SPEC.md` §3: "Right inspector panel
 * (slide-in, appears on node selection)"), hosting whichever `DatasetPanel`/`FeaturePanel`/
 * `QualityPanel`/`CorrelationPanel`/`MLPanel`/`AIInsightPanel` matches the current
 * selection. Framer Motion is already a project dependency (Phase 01) — no new one added.
 */
export function DetailPanel({
  open,
  onClose,
  title,
  subtitle,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <AnimatePresence>
      {open && (
        <motion.aside
          role="complementary"
          aria-label={title}
          initial={{ x: 32, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 32, opacity: 0 }}
          transition={{ duration: 0.22, ease: "easeOut" }}
          className="flex h-full w-full max-w-md flex-col overflow-y-auto border-l border-white/10 bg-surface-raised/95 p-5 backdrop-blur"
        >
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
              {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close panel"
              className="rounded-md border border-white/10 px-2 py-1 text-xs text-slate-400 transition hover:border-accent hover:text-accent"
            >
              Esc ✕
            </button>
          </div>
          {children}
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
