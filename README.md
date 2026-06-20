# ShopMind AI — Agente RAG de Recomendación E-commerce

> Agente de inteligencia artificial que analiza comportamiento de usuarios en e-commerce y responde preguntas en lenguaje natural, combinando RAG (Retrieval-Augmented Generation), tool calling y análisis de datos con pandas. Expuesto como API REST con FastAPI.

![Status](https://img.shields.io/badge/status-completado-success)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688)
![ChromaDB](https://img.shields.io/badge/ChromaDB-vector%20store-orange)

---

## ¿Qué hace este proyecto?

ShopMind AI es un agente conversacional que responde preguntas sobre un catálogo real de e-commerce (32.000+ productos, dataset Olist) combinando tres capacidades:

- **Búsqueda semántica (RAG)** — encuentra productos relevantes aunque la consulta no use las palabras exactas del catálogo
- **Análisis estadístico** — calcula métricas agregadas por categoría (precio, rating, tasa de reseñas positivas) directamente con pandas
- **Auto-corrección** — si una categoría no existe, el agente consulta la lista real de categorías disponibles en vez de inventar una respuesta

Ejemplos de uso:

- *"¿Qué productos de electrónica tienen mejor rating?"*
- *"Analiza la categoría sports"*
- *"¿Qué categorías existen?"*

El agente decide de forma autónoma qué herramienta usar en cada turno, encadenando múltiples llamadas si es necesario (agentic loop).

---

## Arquitectura

```
Cliente (curl / Swagger UI / futuro frontend)
        │
        ▼
  ┌─────────────┐
  │  FastAPI     │  ← POST /ask, GET /health
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │   Agente    │  ← Gemini 2.5 Flash + tool calling (agentic loop)
  └──────┬──────┘
         │
    ┌────┼────────────┐
    │    │             │
    ▼    ▼             ▼
┌───────┐ ┌──────────┐ ┌─────────────────┐
│  RAG  │ │  Pandas  │ │ list_categories │
│ChromaDB│ │ Analysis │ │  (fallback)      │
└───┬───┘ └──────────┘ └─────────────────┘
    │
    ▼
sentence-transformers (all-MiniLM-L6-v2)
    │
    ▼
Dataset: Olist Brazilian E-Commerce (Kaggle, 32K+ productos)
```

### Flujo de datos

```
RAW (9 CSVs Kaggle) → pandas EDA/limpieza → product_summary.csv
        → vectorización (sentence-transformers) → ChromaDB
        → agente consulta vía tool calling → respuesta en lenguaje natural
```

---

## Stack Tecnológico

| Capa | Tecnología | Por qué |
|------|-----------|---------|
| LLM + Tool Calling | Google Gemini 2.5 Flash | Free tier generoso, function calling nativo |
| RAG / Vector Store | ChromaDB + sentence-transformers | Embeddings locales, sin costo, persistente en disco |
| Análisis de datos | Pandas, NumPy | Limpieza, agregaciones, generación de documentos para RAG |
| API | FastAPI + Pydantic | Validación automática, docs interactivas (Swagger) |
| Dataset | Olist Brazilian E-Commerce (Kaggle) | Datos reales de e-commerce: pedidos, reviews, productos |
| Prompts | Archivos `.md` versionados | Buenas prácticas de prompt engineering en producción |

---

## Estructura del Proyecto

```
shopmind-ai/
├── data/
│   ├── raw/                    # CSVs originales de Kaggle (no versionado)
│   └── processed/              # product_summary.csv (sí versionado)
├── notebooks/
│   └── 01_eda.ipynb            # EDA, limpieza y generación de documentos RAG
├── src/
│   ├── agent/
│   │   └── agent.py            # Agentic loop + 3 herramientas (tool calling)
│   ├── rag/
│   │   ├── vectorize.py        # Indexación inicial en ChromaDB
│   │   └── retriever.py        # Búsqueda semántica
│   └── api/
│       └── main.py             # FastAPI: endpoints /ask, /health
├── prompts/
│   └── agent_system.md         # System prompt versionado
├── chroma_db/                  # Vector store persistente (generado localmente)
├── requirements.txt
└── README.md
```

---

## Fases del Proyecto

- **Fase 1** — EDA y limpieza con pandas: consolidación de 5 tablas, generación de `product_summary.csv` (32.216 productos)
- **Fase 2** — RAG Core: vectorización con `sentence-transformers` + indexación en ChromaDB
- **Fase 3** — Agente con tool calling: 3 herramientas (`search_products`, `analyze_category`, `list_categories`) con agentic loop
- **Fase 4** — API REST con FastAPI: endpoints documentados, validación con Pydantic, CORS

---

## Instalación

```bash
git clone https://github.com/Carlos-Maliqueo/shopmind-ai.git
cd shopmind-ai

python -m venv venv
source venv/Scripts/activate    # Windows (Git Bash)
# source venv/bin/activate      # Linux/Mac

pip install -r requirements.txt

# Configurar API key de Gemini (gratis en https://aistudio.google.com/apikey)
echo "GEMINI_API_KEY=tu_api_key_aqui" > .env
```

### Descargar el dataset

Descarga **[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)** y coloca los CSVs en `data/raw/`.

### Ejecutar el pipeline completo

```bash
# 1. Correr el EDA y generar product_summary.csv
jupyter notebook notebooks/01_eda.ipynb

# 2. Vectorizar e indexar en ChromaDB (una sola vez)
PYTHONPATH=. python src/rag/vectorize.py

# 3a. Probar el agente por CLI
PYTHONPATH=. python src/agent/agent.py

# 3b. O levantar la API
PYTHONPATH=. python -m uvicorn src.api.main:app --reload
# Documentación interactiva en http://localhost:8000/docs
```

---

## Uso de la API

```bash
curl -X POST 'http://localhost:8000/ask' \
  -H 'Content-Type: application/json' \
  -d '{"question": "¿Qué productos de electrónica tienen mejor rating?"}'
```

```json
{
  "question": "¿Qué productos de electrónica tienen mejor rating?",
  "answer": "Aquí tienes algunos productos de electrónica con buen rating: ..."
}
```

---

## Conceptos Clave Demostrados

**RAG (Retrieval-Augmented Generation):** en lugar de depender solo del conocimiento del LLM, el agente recupera información real del catálogo antes de responder, evitando alucinaciones sobre productos que no existen.

**Tool Calling / Agentic Loop:** el agente decide autónomamente qué herramienta invocar y puede encadenar múltiples llamadas en un mismo turno (por ejemplo, listar categorías cuando una búsqueda falla, y luego reintentar con la categoría correcta).

**Prompt Engineering en producción:** el system prompt vive en un archivo `.md` versionado, separado del código, facilitando iteración sin tocar lógica de negocio.

**Manejo de datos del mundo real:** el dataset es de e-commerce brasileño con categorías parcialmente traducidas; el proyecto documenta y maneja explícitamente esa limitación en vez de ignorarla.

---

## Limitaciones Conocidas

- El dataset Olist es brasileño; algunas categorías no tienen traducción al inglés y quedan en portugués, lo que puede afectar matches semánticos para búsquedas muy específicas en español/inglés.
- ChromaDB corre en modo local/persistente (no hay un vector store gestionado en la nube); para producción a escala se recomendaría Pinecone, Weaviate o pgvector.
- El agente no tiene memoria entre sesiones de API (cada request es independiente); se podría extender con un historial de conversación por usuario.

---

## Autor

**Carlos Maliqueo Quijano**
Ingeniero Civil en Informática y Telecomunicaciones
[LinkedIn](https://www.linkedin.com/in/carlos-maliqueo-quijano-20b3792a9/) | [GitHub](https://github.com/Carlos-Maliqueo/)
