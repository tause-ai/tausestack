class MCPException(Exception):
    """Excepción base para errores MCP."""
    pass

class MCPInvalidMessageError(MCPException):
    pass

class MCPProviderError(MCPException):
    pass
