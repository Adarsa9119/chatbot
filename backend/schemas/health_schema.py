"""health_schema.py"""
from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    database: str
    embedding_model: str
    version: str = "1.0.0"