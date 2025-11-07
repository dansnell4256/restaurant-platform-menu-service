"""Health check endpoint for service monitoring.

This module provides a simple health check endpoint:
- GET /health - Returns service health status

This endpoint does NOT require authentication and is used by:
- AWS Application Load Balancer health checks
- Kubernetes liveness/readiness probes
- Monitoring and alerting systems
"""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and configure FastAPI application for health checks.

    Returns:
        Configured FastAPI application with health endpoint
    """
    app = FastAPI(
        title="Restaurant Menu Service - Health",
        description="Health check endpoint for monitoring",
        version="0.1.0",
    )

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint for monitoring and load balancers.

        This endpoint does not require authentication and returns the service status.
        Used by AWS ALB health checks, monitoring systems, and orchestration tools.

        Returns:
            Dictionary with status, service name, and version
        """
        return {
            "status": "ok",
            "service": "menu-service",
            "version": "0.1.0",
        }

    return app
