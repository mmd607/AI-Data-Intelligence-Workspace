import { NavLink } from "react-router-dom";

export interface TabItem {
  to: string;
  label: string;
  end?: boolean;
}

export function Tabs({ items }: { items: TabItem[] }) {
  return (
    <nav className="flex gap-1 border-b border-white/10" aria-label="Dataset workspace sections">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) =>
            `rounded-t-md px-3 py-2 text-sm font-medium transition ${
              isActive ? "border-b-2 border-accent text-slate-100" : "text-slate-500 hover:text-slate-300"
            }`
          }
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
