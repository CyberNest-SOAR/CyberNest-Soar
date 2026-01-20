import { Shield } from "lucide-react";
import { cn } from "@/lib/utils";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
  className?: string;
}

export function Logo({ size = "md", showText = true, className }: LogoProps) {
  const sizeClasses = {
    sm: "w-8 h-8",
    md: "w-10 h-10",
    lg: "w-16 h-16",
  };

  const iconSizes = {
    sm: "h-4 w-4",
    md: "h-5 w-5",
    lg: "h-8 w-8",
  };

  const textSizes = {
    sm: "text-lg",
    md: "text-xl",
    lg: "text-3xl",
  };

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div
        className={cn(
          "relative flex items-center justify-center rounded-xl bg-gradient-to-br from-cyber-blue via-primary to-cyber-green p-0.5 shadow-lg",
          sizeClasses[size]
        )}
      >
        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-cyber-blue/20 to-cyber-green/20 blur-md" />
        <div className="relative flex h-full w-full items-center justify-center rounded-[10px] bg-background/90 backdrop-blur-sm">
          <Shield className={cn("text-cyber-blue", iconSizes[size])} />
        </div>
      </div>
      {showText && (
        <div className="flex flex-col">
          <span
            className={cn(
              "font-grotesk font-bold tracking-tight bg-gradient-to-r from-cyber-blue to-cyber-green bg-clip-text text-transparent",
              textSizes[size]
            )}
          >
            CyberNest
          </span>
          <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
            SOAR Platform
          </span>
        </div>
      )}
    </div>
  );
}
