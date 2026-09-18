import { Html } from "@react-three/drei";

/** A billboard 2D label anchored to a 3D point — real DOM text (so it stays sharp,
 * respects the `font-sans`/`font-mono` tokens, and never needs 3D font-glyph loading). */
export function NodeLabel({
  label,
  sub,
  emphasized,
  muted,
}: {
  label: string;
  sub?: string;
  emphasized?: boolean;
  muted?: boolean;
}) {
  return (
    <Html center distanceFactor={9} sprite occlude={false} style={{ pointerEvents: "none" }}>
      <div
        className={`whitespace-nowrap rounded-md px-2 py-1 text-center font-sans transition-opacity ${
          emphasized ? "bg-surface/90 opacity-100" : muted ? "opacity-40" : "opacity-70"
        }`}
      >
        <div className={`text-[11px] font-medium ${emphasized ? "text-slate-100" : "text-slate-300"}`}>{label}</div>
        {sub && <div className="font-mono text-[9px] text-slate-500">{sub}</div>}
      </div>
    </Html>
  );
}
