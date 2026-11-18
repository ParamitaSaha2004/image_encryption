"""
HICE Application Runner
Starts the FastAPI application server with Uvicorn.
"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"[*] Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
    print(f"[*] API Documentation available at: http://{settings.HOST}:{settings.PORT}/docs")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
