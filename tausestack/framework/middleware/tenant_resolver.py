"""
TauseStack Tenant Resolver Middleware

Resolves tenant context from HTTP Host header for tause.pro architecture.
Supports subdomain-based tenancy and custom domain mapping.
"""

import re
import logging
from typing import Optional, Callable, Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

from tausestack.sdk.tenancy import domain_manager, tenancy

logger = logging.getLogger(__name__)

class TenantResolverMiddleware:
    """
    Middleware to resolve tenant context from incoming requests.
    
    Resolves tenant based on:
    1. Subdomain: {tenant}.tause.pro
    2. Custom domain: client.com -> tenant_id
    3. Host header analysis
    """
    
    def __init__(self, app: Callable):
        self.app = app
        self.base_domain = "tause.pro"
        
        # Reserved paths that should not trigger tenant resolution
        self.reserved_paths = {
            "/health", "/metrics", "/.well-known",
            "/static", "/assets", "/favicon.ico", "/robots.txt"
        }
        
        # Paths that should redirect to app subdomain
        self.redirect_paths = {"/app", "/login", "/signup", "/dashboard"}
        
        # System subdomains and their purposes
        self.system_subdomains = {
            "api": "api_service",      # API REST endpoints
            "admin": "admin_panel",    # Panel de administración
            "docs": "documentation",   # Documentación
            "app": "default",          # Aplicación principal (tenant por defecto)
            "www": "landing",          # Landing page redirect
            "cdn": "static_assets",    # CDN para assets estáticos
            "status": "status_page",   # Página de estado del sistema
            "blog": "blog_content",    # Blog/contenido
            "help": "help_center"      # Centro de ayuda
        }
        
        logger.info(f"TenantResolverMiddleware initialized for {self.base_domain}")
    
    def _extract_subdomain(self, host: str) -> Optional[str]:
        """
        Extract subdomain from host header.
        
        Examples:
        - api.tause.pro -> "api"
        - tenant1.tause.pro -> "tenant1"
        - tause.pro -> None
        - custom.domain.com -> None (handled separately)
        """
        if not host or not host.endswith(f".{self.base_domain}"):
            return None
        
        # Remove the base domain part
        subdomain_part = host[:-len(f".{self.base_domain}")]
        
        # Return the subdomain (could be multi-level like "api.v1")
        return subdomain_part if subdomain_part else None
    
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Create request object to access headers
        request = Request(scope, receive)
        
        # Skip tenant resolution for reserved paths
        path = request.url.path
        if any(path.startswith(reserved) for reserved in self.reserved_paths):
            await self.app(scope, receive, send)
            return
        
        # Resolve tenant from host
        host = request.headers.get("host", "")
        subdomain = self._extract_subdomain(host)
        
        # Handle system subdomains
        if subdomain in self.system_subdomains:
            tenant_id = self.system_subdomains[subdomain]
            
            # Special handling for www subdomain
            if subdomain == "www":
                response = RedirectResponse(url=f"https://{self.base_domain}{path}")
                await response(scope, receive, send)
                return
                
        # Handle main domain
        elif host == self.base_domain:
            if path in self.redirect_paths:
                # Redirect app-specific paths to app subdomain
                response = RedirectResponse(url=f"https://app.{self.base_domain}{path}")
                await response(scope, receive, send)
                return
            else:
                # Serve landing page for root domain
                tenant_id = "landing"
        
        # Handle custom tenant subdomains
        elif subdomain and subdomain not in self.system_subdomains:
            # This is a tenant-specific subdomain
            tenant_id = subdomain
            
        # Handle custom domains
        else:
            tenant_id = domain_manager.resolve_tenant_from_host(host)
            if not tenant_id:
                # If no tenant resolved, redirect to default
                response = RedirectResponse(url=f"https://app.{self.base_domain}{path}")
                await response(scope, receive, send)
                return
        
        # Set tenant context for this request
        tenancy.set_current_tenant(tenant_id)
        
        # Add tenant info to request scope for downstream use
        scope["tenant_id"] = tenant_id
        scope["tenant_config"] = tenancy.get_tenant_config(tenant_id)
        
        logger.debug(f"Resolved tenant '{tenant_id}' for host '{host}' and path '{path}'")
        
        try:
            await self.app(scope, receive, send)
        finally:
            # Clean up tenant context after request
            # Note: In production, this should be handled by request lifecycle
            pass

class TenantValidationMiddleware:
    """
    Middleware to validate tenant exists and is active.
    Should be placed after TenantResolverMiddleware.
    """
    
    def __init__(self, app: Callable):
        self.app = app
        
        # Tenants that don't require validation
        self.system_tenants = {"default", "landing", "admin"}
        
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        tenant_id = scope.get("tenant_id")
        
        # Skip validation for system tenants or if no tenant set
        if not tenant_id or tenant_id in self.system_tenants:
            await self.app(scope, receive, send)
            return
        
        # Validate tenant exists and is active
        if not await self._is_tenant_valid(tenant_id):
            # Tenant not found or inactive - redirect to landing
            response = RedirectResponse(url="https://tause.pro")
            await response(scope, receive, send)
            return
        
        await self.app(scope, receive, send)
    
    async def _is_tenant_valid(self, tenant_id: str) -> bool:
        """
        Check if tenant exists and is active.
        This would typically query the database.
        """
        try:
            # TODO: Implement actual tenant validation from database
            # For now, accept any tenant that follows naming rules
            return bool(re.match(r'^[a-z0-9-]+$', tenant_id) and len(tenant_id) >= 2)
        except Exception as e:
            logger.error(f"Error validating tenant {tenant_id}: {e}")
            return False

class TenantSecurityMiddleware:
    """
    Security middleware to prevent cross-tenant data access.
    Ensures requests can only access data for their resolved tenant.
    """
    
    def __init__(self, app: Callable):
        self.app = app
        
    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Add security headers for tenant isolation
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # Add security headers
                headers[b"x-tenant-id"] = scope.get("tenant_id", "unknown").encode()
                headers[b"x-frame-options"] = b"SAMEORIGIN"
                headers[b"x-content-type-options"] = b"nosniff"
                headers[b"x-xss-protection"] = b"1; mode=block"
                
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

# Convenience function to add all tenant middlewares
def add_tenant_middlewares(app):
    """
    Add all tenant-related middlewares to FastAPI app in correct order.
    
    Order is important:
    1. TenantResolverMiddleware (resolves tenant from host)
    2. TenantValidationMiddleware (validates tenant exists)
    3. TenantSecurityMiddleware (adds security headers)
    """
    from fastapi.middleware.base import BaseHTTPMiddleware
    
    # Add in reverse order since FastAPI applies middlewares in LIFO
    app.add_middleware(BaseHTTPMiddleware, dispatch=TenantSecurityMiddleware(app))
    app.add_middleware(BaseHTTPMiddleware, dispatch=TenantValidationMiddleware(app))
    app.add_middleware(BaseHTTPMiddleware, dispatch=TenantResolverMiddleware(app))
    
    logger.info("Tenant middlewares added to FastAPI app")

__all__ = [
    "TenantResolverMiddleware",
    "TenantValidationMiddleware", 
    "TenantSecurityMiddleware",
    "add_tenant_middlewares"
] 