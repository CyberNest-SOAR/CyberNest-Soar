import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Logo } from "./Logo";

const loadingSteps = [
  "INITIALIZING_CORE_SYSTEM",
  "MOUNTING_SECURITY_MODES",
  "ESTABLISHING_ENCRYPTED_TUNNEL",
  "CONNECTING_TO_AI_NEURAL_NETWORK",
  "VALIDATING_OPERATOR_CREDENTIALS",
  "SYSTEM_STABLE_READY",
];

export const CyberLoader = () => {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStep((s) => (s < loadingSteps.length - 1 ? s + 1 : s));
    }, 600);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-background overflow-hidden">
      {/* Background Decor */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px]" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:40px_40px] opacity-[0.03]" />
      </div>

      <div className="relative z-10 w-full max-w-md px-8 space-y-12">
        {/* Logo Animation */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <Logo size="xl" />
        </motion.div>

        {/* Terminal Loading Area */}
        <div className="space-y-6">
          <div className="h-[120px] flex flex-col justify-end space-y-2 font-mono text-[11px] tracking-wider text-muted-foreground/60">
            {loadingSteps.slice(0, step + 1).map((s, i) => (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                key={i}
                className="flex items-center gap-3"
              >
                <span className="text-primary opacity-40 font-bold">{">"}</span>
                <span className={i === step ? "text-foreground font-bold" : ""}>{s}</span>
                {i === step && (
                  <motion.div
                    animate={{ opacity: [0, 1, 0] }}
                    transition={{ duration: 0.8, repeat: Infinity }}
                    className="w-1.5 h-3 bg-primary"
                  />
                )}
              </motion.div>
            ))}
          </div>

          {/* Progress Indicator */}
          <div className="space-y-3">
            <div className="flex justify-between text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/40">
              <span>Initializing Core</span>
              <span>{Math.round(((step + 1) / loadingSteps.length) * 100)}%</span>
            </div>
            <div className="h-1.5 w-full bg-muted/20 rounded-full overflow-hidden p-[1px]">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${((step + 1) / loadingSteps.length) * 100}%` }}
                className="h-full bg-primary rounded-full shadow-[0_0_15px_rgba(99,102,241,0.5)]"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Security notice footer */}
      <motion.p 
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.3 }}
        transition={{ delay: 1 }}
        className="fixed bottom-12 text-[10px] font-black uppercase tracking-[0.4em] text-muted-foreground"
      >
        Encrypted Session Protocol v4.2 // RSA_4096
      </motion.p>
    </div>
  );
};
