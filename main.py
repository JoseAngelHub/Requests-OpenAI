from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.login import app as login_router
from routers.process import app as query_router
import core.logger as J

# api instace
app = FastAPI(
    title="OCR IA API",
    description="API para interpretar preguntas en lenguaje natural y consultar una base de datos SQL.",
    version="1.0.0",
)

origins = ["*"]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# endpoints
app.include_router(login_router, prefix="/login", tags=["Login"])
app.include_router(query_router, prefix="/process", tags=["SQL Assistant"])

# root
@app.get("/")
async def root():
    return {"message": "Bienvenido a la API de consultas SQL con IA"}