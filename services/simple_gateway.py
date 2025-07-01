#!/usr/bin/env python3
"""
Simple API Gateway - TauseStack v0.6.0
Versión simplificada para demo local
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(
    title="TauseStack API Gateway",
    description="Gateway unificado para servicios multi-tenant",
    version="0.6.0"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def gateway_root():
    """Información del gateway."""
    return {
        "service": "TauseStack API Gateway",
        "version": "0.6.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "services": ["analytics", "communications", "billing", "mcp_server"],
        "documentation": "/docs"
    }

@app.get("/health")
async def gateway_health():
    """Health check simplificado."""
    return {
        "gateway": {
            "status": "healthy",
            "version": "0.6.0",
            "uptime": "running",
            "total_requests": 42,
            "success_rate": 99.2,
            "avg_response_time": 0.145
        },
        "services": {
            "analytics": {
                "status": "healthy",
                "response_time": 0.123,
                "last_check": datetime.utcnow().isoformat()
            },
            "communications": {
                "status": "healthy", 
                "response_time": 0.089,
                "last_check": datetime.utcnow().isoformat()
            },
            "billing": {
                "status": "healthy",
                "response_time": 0.156,
                "last_check": datetime.utcnow().isoformat()
            },
            "mcp_server": {
                "status": "healthy",
                "response_time": 0.234,
                "last_check": datetime.utcnow().isoformat()
            }
        },
        "overall_status": "healthy"
    }

@app.get("/metrics")
async def gateway_metrics():
    """Métricas simplificadas."""
    return {
        "gateway_metrics": {
            "total_requests": 156,
            "successful_requests": 154,
            "failed_requests": 2,
            "avg_response_time": 0.145,
            "tenant_usage": {
                "premium-corp": 65,
                "basic-startup": 41,
                "enterprise-bank": 50
            },
            "start_time": datetime.utcnow().isoformat()
        },
        "tenant_usage": {
            "premium-corp": 65,
            "basic-startup": 41,
            "enterprise-bank": 50
        },
        "rate_limits": {
            "premium-corp": {
                "analytics": 23,
                "communications": 12,
                "billing": 8,
                "mcp_server": 22
            },
            "basic-startup": {
                "analytics": 15,
                "communications": 8,
                "billing": 0,
                "mcp_server": 18
            },
            "enterprise-bank": {
                "analytics": 20,
                "communications": 10,
                "billing": 5,
                "mcp_server": 15
            }
        }
    }

@app.get("/admin/tenants")
async def list_tenants():
    """Lista de tenants."""
    return {
        "tenants": ["premium-corp", "basic-startup", "enterprise-bank"],
        "total_tenants": 3,
        "usage_stats": {
            "premium-corp": 8542,
            "basic-startup": 3241,
            "enterprise-bank": 4064
        }
    }

@app.get("/admin/tenants/{tenant_id}/stats")
async def tenant_stats(tenant_id: str):
    """Stats de un tenant específico."""
    return {
        "tenant_id": tenant_id,
        "total_requests": 8542 if tenant_id == "premium-corp" else 3241,
        "rate_limits": {
            "analytics": 23,
            "communications": 12,
            "billing": 8,
            "mcp_server": 22
        },
        "services_used": ["analytics", "communications", "billing", "mcp_server"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000) 