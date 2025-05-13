from abc import ABC, abstractmethod
from typing import Dict, Any, List

class MCPServer(ABC):
    """
    Interfaz abstracta para servidores MCP (Multi-Call Protocol).
    
    Esta clase define el contrato que todos los servidores MCP deben implementar,
    permitiendo exponer herramientas y funcionalidades a clientes externos.
    """
    
    @abstractmethod
    async def register_tool(self, tool_name: str, tool_config: Dict[str, Any]) -> bool:
        """
        Registra una nueva herramienta en el servidor MCP.
        
        Args:
            tool_name (str): Nombre único de la herramienta.
            tool_config (Dict[str, Any]): Configuración de la herramienta (descripción, parámetros, etc).
            
        Returns:
            bool: True si el registro fue exitoso, False en caso contrario.
        """
        pass
    
    @abstractmethod
    async def unregister_tool(self, tool_name: str) -> bool:
        """
        Elimina una herramienta registrada del servidor MCP.
        
        Args:
            tool_name (str): Nombre de la herramienta a eliminar.
            
        Returns:
            bool: True si la eliminación fue exitosa, False en caso contrario.
        """
        pass
    
    @abstractmethod
    async def handle_call(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja una llamada entrante a una herramienta registrada.
        
        Args:
            tool_name (str): Nombre de la herramienta llamada.
            params (Dict[str, Any]): Parámetros de la llamada.
            
        Returns:
            Dict[str, Any]: Resultado de la ejecución de la herramienta.
        """
        pass
    
    @abstractmethod
    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de herramientas registradas en el servidor.
        
        Returns:
            List[Dict[str, Any]]: Lista de herramientas disponibles con sus configuraciones.
        """
        pass
    
    @abstractmethod
    async def generate_manifest(self) -> Dict[str, Any]:
        """
        Genera el manifiesto del servidor MCP con todas sus herramientas y configuraciones.
        
        Returns:
            Dict[str, Any]: Manifiesto completo del servidor MCP.
        """
        pass
