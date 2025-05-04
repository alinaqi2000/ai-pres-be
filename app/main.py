from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime
from typing import Any

from config import DEBUG, APP_HOST, APP_PORT
from database.init import Base, engine
from routes import auth_routes, role_routes, property_routes

def custom_json_encoder(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Pres API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(role_routes.router)
app.include_router(property_routes.router)


@app.get("/")
def read_root():
    return {"name": "AI Pres API", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=True, debug=DEBUG)

    