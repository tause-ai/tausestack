#!/usr/bin/env python3
"""
API Gateway - TauseStack v0.6.0
Gateway unificado para todos los servicios multi-tenant
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict
import time
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de servicios
SERVICES_CONFIG = {
    "analytics": {
        "url": "http://localhost:8001",
        "health_endpoint": "/health",
        "rate_limit": 1000,  # requests per hour per tenant
        "timeout": 30
    },
    "communications": {
        "url": "http://localhost:8002", 
        "health_endpoint": "/health",
        "rate_limit": 500,
        "timeout": 30
    },
    "billing": {
        "url": "http://localhost:8003",
        "health_endpoint": "/health", 
        "rate_limit": 200,
        "timeout": 30
    },
    "mcp_server": {
        "url": "http://localhost:8000",
        "health_endpoint": "/health",
        "rate_limit": 2000,
        "timeout": 45
    }
}

# Rate limiting storage
rate_limit_storage = defaultdict(lambda: defaultdict(list))

# Métricas globales
gateway_metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "avg_response_time": 0,
    "services_health": {},
    "tenant_usage": defaultdict(int),
    "start_time": datetime.utcnow()
}

app = FastAPI(
    title="TauseStack API Gateway",
    description="Gateway unificado para servicios multi-tenant",
    version="0.6.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # En producción, especificar hosts
)

class RateLimitExceeded(Exception):
    pass

class ServiceUnavailable(Exception):
    pass

def get_tenant_id(request: Request) -> str:
    """Extrae el tenant_id del request."""
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        # Fallback a query parameter
        tenant_id = request.query_params.get("tenant_id")
    if not tenant_id:
        tenant_id = "default"
    return tenant_id

def check_rate_limit(tenant_id: str, service: str) -> bool:
    """Verifica rate limiting por tenant y servicio."""
    if service not in SERVICES_CONFIG:
        return False
    
    limit = SERVICES_CONFIG[service]["rate_limit"]
    now = time.time()
    hour_ago = now - 3600
    
    # Limpiar requests antiguos
    rate_limit_storage[tenant_id][service] = [
        timestamp for timestamp in rate_limit_storage[tenant_id][service] 
        if timestamp > hour_ago
    ]
    
    # Verificar límite
    if len(rate_limit_storage[tenant_id][service]) >= limit:
        return False
    
    # Registrar request
    rate_limit_storage[tenant_id][service].append(now)
    return True

async def forward_request(
    service: str, 
    path: str, 
    method: str, 
    headers: Dict[str, str], 
    body: Optional[bytes] = None,
    params: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Reenvía request al servicio correspondiente."""
    if service not in SERVICES_CONFIG:
        raise HTTPException(status_code=404, detail=f"Service {service} not found")
    
    service_config = SERVICES_CONFIG[service]
    url = f"{service_config['url']}{path}"
    timeout = service_config["timeout"]
    
    # Preparar headers
    forward_headers = {k: v for k, v in headers.items() if k.lower() not in ['host', 'content-length']}
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=forward_headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=forward_headers, content=body, params=params)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=forward_headers, content=body, params=params)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=forward_headers, params=params)
            elif method.upper() == "PATCH":
                response = await client.patch(url, headers=forward_headers, content=body, params=params)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            response_time = time.time() - start_time
            
            # Actualizar métricas
            gateway_metrics["total_requests"] += 1
            if response.status_code < 400:
                gateway_metrics["successful_requests"] += 1
            else:
                gateway_metrics["failed_requests"] += 1
            
            # Actualizar tiempo promedio de respuesta
            current_avg = gateway_metrics["avg_response_time"]
            total_requests = gateway_metrics["total_requests"]
            gateway_metrics["avg_response_time"] = (current_avg * (total_requests - 1) + response_time) / total_requests
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.content,
                "response_time": response_time
            }
            
    except httpx.TimeoutException:
        gateway_metrics["failed_requests"] += 1
        raise HTTPException(status_code=504, detail=f"Service {service} timeout")
    except httpx.ConnectError:
        gateway_metrics["failed_requests"] += 1
        raise HTTPException(status_code=503, detail=f"Service {service} unavailable")
    except Exception as e:
        gateway_metrics["failed_requests"] += 1
        logger.error(f"Error forwarding to {service}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal gateway error")

@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    """Middleware principal del gateway."""
    start_time = time.time()
    
    # Extraer tenant_id
    tenant_id = get_tenant_id(request)
    
    # Actualizar métricas de tenant
    gateway_metrics["tenant_usage"][tenant_id] += 1
    
    response = await call_next(request)
    
    # Agregar headers de respuesta
    response.headers["X-Gateway-Version"] = "0.6.0"
    response.headers["X-Tenant-ID"] = tenant_id
    response.headers["X-Response-Time"] = str(time.time() - start_time)
    
    return response

# === RUTAS DEL GATEWAY ===

@app.get("/")
async def gateway_root():
    """Información del gateway."""
    return {
        "service": "TauseStack API Gateway",
        "version": "0.6.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "services": list(SERVICES_CONFIG.keys()),
        "documentation": "/docs"
    }

@app.get("/health")
async def gateway_health():
    """Health check del gateway y servicios."""
    services_health = {}
    
    # Verificar salud de cada servicio
    for service_name, config in SERVICES_CONFIG.items():
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{config['url']}{config['health_endpoint']}")
                services_health[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds() if response.elapsed else 0,
                    "last_check": datetime.utcnow().isoformat()
                }
        except Exception as e:
            services_health[service_name] = {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    gateway_metrics["services_health"] = services_health
    
    # Determinar estado general
    all_healthy = all(s["status"] == "healthy" for s in services_health.values())
    
    return {
        "gateway": {
            "status": "healthy",
            "version": "0.6.0",
            "uptime": str(datetime.utcnow() - gateway_metrics["start_time"]),
            "total_requests": gateway_metrics["total_requests"],
            "success_rate": gateway_metrics["successful_requests"] / max(gateway_metrics["total_requests"], 1) * 100,
            "avg_response_time": gateway_metrics["avg_response_time"]
        },
        "services": services_health,
        "overall_status": "healthy" if all_healthy else "degraded"
    }

@app.get("/metrics")
async def gateway_metrics_endpoint():
    """Métricas del gateway."""
    return {
        "gateway_metrics": gateway_metrics,
        "tenant_usage": dict(gateway_metrics["tenant_usage"]),
        "rate_limits": {
            tenant: {service: len(requests) for service, requests in services.items()}
            for tenant, services in rate_limit_storage.items()
        }
    }

# === RUTAS DE SERVICIOS ===

@app.api_route("/analytics/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def analytics_proxy(path: str, request: Request):
    """Proxy para el servicio de Analytics."""
    tenant_id = get_tenant_id(request)
    
    # Verificar rate limiting
    if not check_rate_limit(tenant_id, "analytics"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for analytics service")
    
    # Leer body si existe
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    
    # Reenviar request
    result = await forward_request(
        "analytics", 
        f"/{path}", 
        request.method, 
        dict(request.headers),
        body,
        dict(request.query_params)
    )
    
    return Response(
        content=result["content"],
        status_code=result["status_code"],
        headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
    )

@app.api_route("/communications/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def communications_proxy(path: str, request: Request):
    """Proxy para el servicio de Communications."""
    tenant_id = get_tenant_id(request)
    
    if not check_rate_limit(tenant_id, "communications"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for communications service")
    
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    
    result = await forward_request(
        "communications", 
        f"/{path}", 
        request.method, 
        dict(request.headers),
        body,
        dict(request.query_params)
    )
    
    return Response(
        content=result["content"],
        status_code=result["status_code"],
        headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
    )

@app.api_route("/billing/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def billing_proxy(path: str, request: Request):
    """Proxy para el servicio de Billing."""
    tenant_id = get_tenant_id(request)
    
    if not check_rate_limit(tenant_id, "billing"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for billing service")
    
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    
    result = await forward_request(
        "billing", 
        f"/{path}", 
        request.method, 
        dict(request.headers),
        body,
        dict(request.query_params)
    )
    
    return Response(
        content=result["content"],
        status_code=result["status_code"],
        headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
    )

@app.api_route("/mcp/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def mcp_proxy(path: str, request: Request):
    """Proxy para el servidor MCP."""
    tenant_id = get_tenant_id(request)
    
    if not check_rate_limit(tenant_id, "mcp_server"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for MCP service")
    
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    
    result = await forward_request(
        "mcp_server", 
        f"/{path}", 
        request.method, 
        dict(request.headers),
        body,
        dict(request.query_params)
    )
    
    return Response(
        content=result["content"],
        status_code=result["status_code"],
        headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
    )

# === RUTAS DE ADMINISTRACIÓN ===

@app.get("/admin/tenants")
async def list_tenants():
    """Lista todos los tenants activos."""
    return {
        "tenants": list(gateway_metrics["tenant_usage"].keys()),
        "total_tenants": len(gateway_metrics["tenant_usage"]),
        "usage_stats": dict(gateway_metrics["tenant_usage"])
    }

@app.get("/admin/tenants/{tenant_id}/stats")
async def tenant_stats(tenant_id: str):
    """Estadísticas de un tenant específico."""
    if tenant_id not in gateway_metrics["tenant_usage"]:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {
        "tenant_id": tenant_id,
        "total_requests": gateway_metrics["tenant_usage"][tenant_id],
        "rate_limits": {
            service: len(requests) 
            for service, requests in rate_limit_storage[tenant_id].items()
        },
        "services_used": list(rate_limit_storage[tenant_id].keys())
    }

@app.post("/admin/tenants/{tenant_id}/reset-limits")
async def reset_tenant_limits(tenant_id: str):
    """Resetea los límites de rate limiting de un tenant."""
    if tenant_id in rate_limit_storage:
        rate_limit_storage[tenant_id].clear()
    
    return {
        "message": f"Rate limits reset for tenant {tenant_id}",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_gateway:app",
        host="0.0.0.0",
        port=9000,
        reload=True,
        log_level="info"
    ) 