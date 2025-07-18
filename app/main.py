from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from datetime import datetime
from typing import Any
import os
from config import UPLOAD_DIR

from config import DEBUG, APP_HOST, APP_PORT
from database.init import Base, engine
from routes import (
    auth_routes,
    property_routes,
    image_routes,
    tenant_request_routes,
    booking_routes,
    invoice_routes,
    payment_routes,
    payment_method_routes,
    report_routes,
)

import logging


def custom_json_encoder(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Pres API")

uploads_dir = os.path.join(os.getcwd(), UPLOAD_DIR)
os.makedirs(uploads_dir, exist_ok=True)

app.mount(f"/{UPLOAD_DIR}", StaticFiles(directory=uploads_dir), name=UPLOAD_DIR)

# Initialize background tasks scheduler
from services.background_tasks import BackgroundTasks
background_tasks = BackgroundTasks()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(property_routes.router)
app.include_router(image_routes.router)
app.include_router(tenant_request_routes.router)
app.include_router(booking_routes.router)
app.include_router(invoice_routes.router)
app.include_router(payment_routes.router)
app.include_router(payment_method_routes.router)
app.include_router(report_routes.router)

@app.get("/")
def read_root():
    return {"name": "AI Pres API", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=True, debug=DEBUG)
