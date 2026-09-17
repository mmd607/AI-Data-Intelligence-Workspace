import type { BadgeTone } from "./Badge";

export function severityToTone(severity: "info" | "warning" | "critical"): BadgeTone {
  if (severity === "critical") return "critical";
  if (severity === "warning") return "warning";
  return "info";
}
