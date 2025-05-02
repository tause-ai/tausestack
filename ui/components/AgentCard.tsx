// Componente de ejemplo siguiendo convención PascalCase
import React from "react";

export interface AgentCardProps {
  name: string;
  status: string;
}

/**
 * Muestra información básica de un agente.
 * @param name Nombre del agente
 * @param status Estado del agente
 */
const AgentCard: React.FC<AgentCardProps> = ({ name, status }) => {
  return (
    <div className="border p-4 rounded shadow bg-white">
      <h2 className="font-bold text-lg">{name}</h2>
      <span className="text-xs text-gray-500">{status}</span>
    </div>
  );
};

export default AgentCard;
