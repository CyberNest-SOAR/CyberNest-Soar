import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface CyberCardProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}

export const CyberCard = ({ children, className, delay = 0 }: CyberCardProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "premium-card overflow-hidden group relative",
        className
      )}
    >
      {/* Subtle top edge highlight */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-primary/20 to-transparent" />
      
      <div className="relative z-10 p-6">
        {children}
      </div>
    </motion.div>
  );
};
