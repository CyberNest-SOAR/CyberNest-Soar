import React, { createContext, useContext } from "react";
import { useServerStatus, ServerStatus } from "@/hooks/useServerStatus";

const ServerStatusContext = createContext<ServerStatus>({
  isOnline: null,
  lastChecked: null,
  latencyMs: null,
  retry: () => {},
});

export const ServerStatusProvider = ({ children }: { children: React.ReactNode }) => {
  const status = useServerStatus();
  return (
    <ServerStatusContext.Provider value={status}>
      {children}
    </ServerStatusContext.Provider>
  );
};

/** Use this hook anywhere to read the shared backend connection state. */
export function useServerStatusContext(): ServerStatus {
  return useContext(ServerStatusContext);
}
