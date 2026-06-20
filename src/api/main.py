"""
Fase 4 — FastAPI: expone el agente ShopMind AI como API REST
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agent.agent import ShopMindAgent

# ── Inicialización ──────────────────────────────────────────────

app = FastAPI(
    title="ShopMind AI API",
    description=(
        "API REST de un agente RAG para análisis de comportamiento "
        "de usuarios en e-commerce. Usa Gemini + ChromaDB + Pandas."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: restringir a dominios específicos
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton del agente — se inicializa una sola vez al arrancar el server
_agent: ShopMindAgent | None = None


def get_agent() -> ShopMindAgent:
    global _agent
    if _agent is None:
        _agent = ShopMindAgent()
    return _agent


# ── Schemas ─────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Pregunta en lenguaje natural sobre productos o categorías",
        examples=["¿Qué productos de electrónica tienen mejor rating?"],
    )


class AskResponse(BaseModel):
    question: str
    answer: str


class HealthResponse(BaseModel):
    status: str
    service: str


# ── Endpoints ───────────────────────────────────────────────────

@app.get("/", response_model=HealthResponse, tags=["Health"])
def root():
    """Endpoint raíz — confirma que el servicio está activo."""
    return HealthResponse(status="ok", service="ShopMind AI API")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check para monitoreo / orquestadores (Docker, K8s, etc)."""
    return HealthResponse(status="ok", service="ShopMind AI API")


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
def ask_agent(request: AskRequest):
    """
    Envía una pregunta en lenguaje natural al agente ShopMind AI.

    El agente decide automáticamente si debe:
    - Buscar productos por similitud semántica (RAG)
    - Analizar estadísticas de una categoría
    - Listar categorías disponibles
    - Responder directamente

    Ejemplo de uso:
    ```
    POST /ask
    {"question": "¿Qué productos de electrónica tienen mejor rating?"}
    ```
    """
    try:
        agent = get_agent()
        answer = agent.run(request.question)
        return AskResponse(question=request.question, answer=answer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando la pregunta: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
