import { useState, useEffect } from "react";

/**
 * Hook personalizado para obtener el estado de un agente.
 * @param agentId ID del agente
 */
export function useAgentStatus(agentId: string) {
  const [status, setStatus] = useState<string>("offline");

  useEffect(() => {
    // Simulación: en producción, llamar a la API
    setStatus(agentId ? "online" : "offline");
  }, [agentId]);

  return status;
}
