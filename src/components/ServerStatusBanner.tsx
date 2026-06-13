import { motion, AnimatePresence } from "framer-motion";
import { WifiOff, RefreshCw, Database, Wifi } from "lucide-react";
import { useServerStatusContext } from "@/contexts/ServerStatusContext";
import { Button } from "@/components/ui/button";
import { useState } from "react";

/**
 * A slim banner rendered at the top of the app content area.
 * - OFFLINE → amber/red warning with "DEMO MODE — Pipeline Snapshot" label
 * - ONLINE  → brief green flash then hides itself
 * - CHECKING → yellow scanning state
 */
export function ServerStatusBanner() {
  const { isOnline, lastChecked, latencyMs, retry } = useServerStatusContext();
  const [retrying, setRetrying] = useState(false);

  const handleRetry = async () => {
    setRetrying(true);
    await retry();
    setRetrying(false);
  };

  // Only show banner when offline or still checking on first load
  const show = isOnline === false || isOnline === null;

  const timeStr = lastChecked
    ? lastChecked.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : null;

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="overflow-hidden"
        >
          <div
            className={`flex items-center justify-between gap-4 px-4 sm:px-6 py-2 text-xs font-bold
              ${
                isOnline === null
                  ? "bg-yellow-500/10 border-b border-yellow-500/30 text-yellow-400"
                  : "bg-rose-500/10 border-b border-rose-500/30 text-rose-400"
              }`}
          >
            {/* Left — status indicator */}
            <div className="flex items-center gap-3 min-w-0">
              <span
                className={`h-2 w-2 rounded-full shrink-0 ${
                  isOnline === null
                    ? "bg-yellow-500 animate-pulse"
                    : "bg-rose-500 animate-pulse"
                }`}
              />

              {isOnline === null ? (
                <span className="uppercase tracking-widest font-black text-[10px]">
                  Scanning backend…
                </span>
              ) : (
                <>
                  <WifiOff className="h-3.5 w-3.5 shrink-0" />
                  <span className="uppercase tracking-widest font-black text-[10px] hidden sm:inline">
                    Offline — Demo Mode
                  </span>
                  <span className="font-mono text-[10px] text-rose-400/70 hidden md:inline">
                    │
                  </span>
                  <Database className="h-3 w-3 shrink-0 hidden md:inline" />
                  <span className="text-[10px] text-rose-300/80 truncate hidden md:inline">
                    Showing pre-generated dataset pipeline snapshot
                  </span>
                </>
              )}
            </div>

            {/* Right — time + retry */}
            <div className="flex items-center gap-3 shrink-0">
              {timeStr && (
                <span className="font-mono text-[9px] opacity-60 hidden sm:inline">
                  Last checked: {timeStr}
                </span>
              )}
              {isOnline === false && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRetry}
                  disabled={retrying}
                  className={`h-6 px-2 text-[9px] uppercase tracking-widest font-black rounded-md
                    border border-rose-500/40 text-rose-400 hover:bg-rose-500/10 hover:text-rose-300
                    transition-all`}
                >
                  <RefreshCw className={`h-3 w-3 mr-1 ${retrying ? "animate-spin" : ""}`} />
                  Retry
                </Button>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* Brief "connected" flash when just came online */}
      {isOnline === true && latencyMs !== null && (
        <motion.div
          key="online-flash"
          initial={{ opacity: 1, height: "auto" }}
          animate={{ opacity: 0, height: 0 }}
          transition={{ delay: 2.5, duration: 0.6 }}
          className="overflow-hidden"
        >
          <div className="flex items-center gap-2 px-4 sm:px-6 py-1.5 bg-emerald-500/10 border-b border-emerald-500/20 text-emerald-400 text-[10px] font-bold">
            <Wifi className="h-3 w-3" />
            <span className="uppercase tracking-widest">Backend Online</span>
            <span className="font-mono opacity-60">— {latencyMs}ms</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
