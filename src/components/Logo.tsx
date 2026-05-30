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
    sm: "h-8",
    md: "h-10",
    lg: "h-16",
    xl: "h-24",
  };

  // theme === "light" ? logoLight (logo for light bg)
  // theme === "dark" ? logoDark (logo for dark bg)
  const logoSrc = theme === "light" ? logoLight : logoDark;

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <img
        src={logoSrc}
        alt="CyberNest Logo"
        className={cn("w-auto object-contain transition-all duration-300", sizeClasses[size])}
      />
    </div>
  );
}

