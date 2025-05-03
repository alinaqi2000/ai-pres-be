from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import DEBUG, APP_HOST, APP_PORT
from database.init import Base, engine
from routes import auth_routes, protected_routes

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
app.include_router(protected_routes.router)


@app.get("/")
def read_root():
    return {"name": "AI Pres API", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=True, debug=DEBUG)

    