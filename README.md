# 🛒 ShopMind AI — Agente RAG de Recomendación E-commerce

> Agente de inteligencia artificial que analiza comportamiento de usuarios en e-commerce y responde preguntas en lenguaje natural usando RAG (Retrieval-Augmented Generation) + LLMs.

---

## 🎯 ¿Qué hace este proyecto?

ShopMind AI permite hacer preguntas como:

- *"¿Qué productos le recomendarías a un usuario que compró auriculares?"*
- *"¿Por qué este producto tiene mala recepción entre los usuarios?"*
- *"¿Cuáles son los productos más comprados por usuarios frecuentes?"*

El agente decide de forma autónoma cuándo buscar en la base vectorial, cuándo ejecutar análisis de datos y cuándo responder directamente, usando **tool calling** con un LLM.

---

## 🏗️ Arquitectura

```
Usuario (query en lenguaje natural)
        │
        ▼
  ┌─────────────┐
  │  FastAPI     │  ← Endpoint /ask
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │   Agente    │  ← Orquesta herramientas (LLM + tool calling)
  └──────┬──────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐  ┌──────────┐
│  RAG  │  │  Pandas  │
│ChromaDB│  │ Analysis │
└───────┘  └──────────┘
    │
    ▼
Embeddings (sentence-transformers)
    │
    ▼
Dataset: Olist Brazilian E-Commerce (Kaggle)
```

### Flujo de datos

```
RAW (CSV Kaggle) → PROCESSED (pandas, limpieza) → VECTORIZADO (ChromaDB) → AGENTE → RESPUESTA
```

---

## 🧰 Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| LLM | Claude API (claude-sonnet) |
| RAG / Vector Store | ChromaDB + sentence-transformers |
| Análisis de datos | Pandas, NumPy |
| API | FastAPI |
| Orquestación agente | Tool calling (Anthropic SDK) |
| Dataset | Olist Brazilian E-Commerce (Kaggle) |
| Infra | Docker, Docker Compose |
| Prompts | Archivos `.md` versionados |

---

## 📁 Estructura del Proyecto

```
shopmind-ai/
├── data/
│   ├── raw/               # CSVs originales de Kaggle (no subir a git)
│   └── processed/         # Datos limpios generados por el notebook
├── notebooks/
│   └── 01_eda.ipynb       # Exploración y limpieza con pandas
├── src/
│   ├── agent/             # Lógica del agente y tool calling
│   ├── rag/               # Vector store, embeddings, retrieval
│   └── api/               # FastAPI endpoints
├── prompts/               # Prompts del agente en archivos .md
├── docs/                  # Diagramas y decisiones de diseño
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🚀 Fases del Proyecto

- [x] **Fase 1** — Estructura del proyecto + EDA con pandas
- [ ] **Fase 2** — RAG Core: embeddings + ChromaDB
- [ ] **Fase 3** — Agente con tool calling
- [ ] **Fase 4** — FastAPI + documentación final

---

## ⚙️ Instalación

```bash
# Clonar el repositorio
git clone https://github.com/Carlos-Maliqueo/shopmind-ai.git
cd shopmind-ai

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu ANTHROPIC_API_KEY
```

---

## 📊 Dataset

Este proyecto usa el dataset **[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)** de Kaggle.

Descarga los archivos CSV y colócalos en `data/raw/`.

---

## 🔑 Conceptos Clave

**RAG (Retrieval-Augmented Generation):** En lugar de depender solo del conocimiento del LLM, el agente recupera información relevante de una base de datos vectorial antes de responder. Esto permite respuestas basadas en datos reales del e-commerce.

**Tool Calling:** El agente tiene acceso a "herramientas" (funciones Python) que puede invocar según necesite: buscar en el vector store, ejecutar análisis pandas, o filtrar productos.

**Prompt Engineering:** Los prompts del sistema están versionados como archivos `.md` para facilitar iteración y control de tokens.

---

## 👤 Autor

**Carlos Maliqueo Quijano**
Ingeniero Civil en Informática y Telecomunicaciones
[LinkedIn](https://www.linkedin.com/in/carlos-maliqueo-quijano-20b3792a9/) | [GitHub](https://github.com/Carlos-Maliqueo/)
# shopmind-ai
