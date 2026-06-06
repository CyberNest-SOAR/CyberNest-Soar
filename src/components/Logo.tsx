import { cn } from "@/lib/utils";
import { useTheme } from "./ThemeProvider";
import logoLight from "../CyberNestLogolight.png";
import logoDark from "../CyberNestLogodark.png";

interface LogoProps {
  size?: "sm" | "md" | "lg" | "xl";
  showText?: boolean;
  className?: string;
}

export function Logo({ size = "md", showText = true, className }: LogoProps) {
  const { theme } = useTheme();

  const sizeClasses = {
    sm: "h-6",
    md: "h-9",
    lg: "h-14",
    xl: "h-20",
  };

  const textClasses = {
    sm: "text-[9px] tracking-[0.3em] mt-1",
    md: "text-[10px] tracking-[0.4em] mt-1.5",
    lg: "text-[12px] tracking-[0.5em] mt-2",
    xl: "text-[16px] tracking-[0.6em] mt-3",
  };

  // theme === "light" ? logoLight (logo for light bg)
  // theme === "dark" ? logoDark (logo for dark bg)
  const logoSrc = theme === "light" ? logoLight : logoDark;

  return (
    <div className={cn("flex flex-col items-center justify-center select-none", className)}>
      <img
        src={logoSrc}
        alt="CyberNest Logo"
        className={cn("w-auto object-contain transition-all duration-300", sizeClasses[size])}
      />
      {showText && (
        <span className={cn("font-black uppercase text-primary italic font-mono leading-none opacity-85", textClasses[size])}>
          SOAR
        </span>
      )}
    </div>
  );
}


