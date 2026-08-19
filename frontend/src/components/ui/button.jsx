import { cn } from "@/lib/utils";

const variants = {
  primary:
    "bg-asta-blueDeep text-asta-white shadow-[0_0_0_1px_theme(colors.asta.blueBright)_inset] hover:bg-asta-blueBright",
  ghost:
    "bg-transparent text-asta-white shadow-[0_0_0_1px_theme(colors.asta.line)_inset] hover:shadow-[0_0_0_1px_theme(colors.asta.yellow)_inset] hover:text-asta-yellow",
  danger:
    "bg-transparent text-asta-whiteDim shadow-[0_0_0_1px_theme(colors.asta.line)_inset] hover:text-asta-red hover:shadow-[0_0_0_1px_theme(colors.asta.red)_inset]",
};

export function Button({
  children,
  variant = "primary",
  className = "",
  chamfer = "12px",
  ...props
}) {
  return (
    <button
      className={cn(
        "inline-flex items-center gap-2 px-5 py-3 font-display text-xs font-bold tracking-wide cursor-pointer transition-all duration-150 hover:-translate-y-0.5",
        variants[variant],
        className
      )}
      style={{
        clipPath: `polygon(${chamfer} 0, 100% 0, 100% calc(100% - ${chamfer}), calc(100% - ${chamfer}) 100%, 0 100%, 0 ${chamfer})`,
      }}
      {...props}
    >
      {children}
    </button>
  );
}
