/**
 * 3D scene interaction state (hover, selection, focus, filters, search, view mode) —
 * Zustand (ADR-008, confirmed this phase), chosen over React Context for its granular
 * subscription model: a component reading only `hoveredNodeId` doesn't re-render when
 * `searchQuery` changes, which matters for a scene with dozens of frequently-updating
 * nodes (`02_DOCS/ARCHITECTURE.md` "3D Interaction & State").
 *
 * This store holds pure UI/interaction state only — never server data (the `UniverseGraph`
 * built by `universe/mapping.ts` is regular React state/derived data in `UniversePage`),
 * matching this project's existing "don't duplicate server state" convention
 * (`state/DatasetSessionContext.tsx`).
 */

import { create } from "zustand";

export type UniverseViewMode = "3d" | "2d";

export interface UniverseFilters {
  numeric: boolean;
  categorical: boolean;
  missing: boolean;
  qualityWarning: boolean;
  correlated: boolean;
  mlRelated: boolean;
}

export const DEFAULT_FILTERS: UniverseFilters = {
  numeric: false,
  categorical: false,
  missing: false,
  qualityWarning: false,
  correlated: false,
  mlRelated: false,
};

export interface UniverseState {
  selectedNodeId: string | null;
  hoveredNodeId: string | null;
  focusedNodeId: string | null;
  searchQuery: string;
  filters: UniverseFilters;
  viewMode: UniverseViewMode;

  selectNode: (id: string | null) => void;
  hoverNode: (id: string | null) => void;
  /** Selecting and focusing together is the common case (click a node -> select + camera
   * eases toward it, §4.4/§4.5); `selectNode` alone stays available for selection without
   * a camera move (e.g. selecting from the 2D fallback list). */
  focusNode: (id: string | null) => void;
  setSearchQuery: (query: string) => void;
  toggleFilter: (key: keyof UniverseFilters) => void;
  clearFilters: () => void;
  setViewMode: (mode: UniverseViewMode) => void;
  /** "Reset View" (§12): clears selection/hover/focus so the camera eases back to the
   * overview framing. Deliberately leaves search/filters/viewMode untouched — those are
   * independent user choices, not part of "where the camera is looking." */
  resetView: () => void;
}

export const useUniverseStore = create<UniverseState>((set) => ({
  selectedNodeId: null,
  hoveredNodeId: null,
  focusedNodeId: null,
  searchQuery: "",
  filters: DEFAULT_FILTERS,
  viewMode: "3d",

  selectNode: (id) => set({ selectedNodeId: id }),
  hoverNode: (id) => set({ hoveredNodeId: id }),
  focusNode: (id) => set({ focusedNodeId: id, selectedNodeId: id }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  toggleFilter: (key) => set((s) => ({ filters: { ...s.filters, [key]: !s.filters[key] } })),
  clearFilters: () => set({ filters: DEFAULT_FILTERS }),
  setViewMode: (mode) => set({ viewMode: mode }),
  resetView: () => set({ selectedNodeId: null, hoveredNodeId: null, focusedNodeId: null }),
}));
