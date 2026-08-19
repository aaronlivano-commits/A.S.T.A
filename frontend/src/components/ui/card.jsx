import { cn } from "@/lib/utils";

// Chamfered "panel-frame" card: a thin line-colored outer wrapper clipped at the
// corners, with an inset panel of the same shape one step smaller inside it —
// mirrors the console panel styling used across the whole app.
export function Card({ children, className = "" }) {
  return (
    <div
      className="bg-asta-line p-px"
      style={{
        clipPath:
          "polygon(18px 0, 100% 0, 100% calc(100% - 18px), calc(100% - 18px) 100%, 0 100%, 0 18px)",
      }}
    >
      <div
        className={cn("bg-asta-panel p-6 md:p-8", className)}
        style={{
          clipPath:
            "polygon(16px 0, 100% 0, 100% calc(100% - 16px), calc(100% - 16px) 100%, 0 100%, 0 16px)",
        }}
      >
        {children}
      </div>
    </div>
  );
}

export function CardHeader({ designation, title }) {
  return (
    <header className="flex items-baseline gap-4 flex-wrap mb-4">
      <span className="font-mono text-xs text-asta-red border border-asta-red px-2 py-0.5"
        style={{ clipPath: "polygon(6px 0, 100% 0, 100% 100%, 0 100%, 0 6px)" }}>
        {designation}
      </span>
      <h2 className="font-display text-xl md:text-2xl text-asta-white m-0">{title}</h2>
    </header>
  );
}
