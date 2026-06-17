"""
Fase 2 — Vectorización e indexación en ChromaDB
Ejecutar una vez: python src/rag/vectorize.py
"""

import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os

# ── Configuración ──────────────────────────────────────────────
PROCESSED_PATH = "data/processed/product_summary.csv"
CHROMA_PATH    = "chroma_db"
COLLECTION     = "products"
MODEL_NAME     = "all-MiniLM-L6-v2"   # modelo liviano y rápido
BATCH_SIZE     = 500

# ── Carga de datos ─────────────────────────────────────────────
print("📂 Cargando product_summary.csv...")
df = pd.read_csv(PROCESSED_PATH)
df = df.dropna(subset=["document"])
print(f"   {len(df):,} productos cargados")

# ── ChromaDB client ────────────────────────────────────────────
print("🗄️  Inicializando ChromaDB...")
client = chromadb.PersistentClient(path=CHROMA_PATH)

# Borra la colección si ya existe (para re-indexar limpio)
try:
    client.delete_collection(COLLECTION)
    print("   Colección anterior eliminada")
except Exception:
    pass

# Función de embedding con sentence-transformers
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=MODEL_NAME
)

collection = client.create_collection(
    name=COLLECTION,
    embedding_function=ef,
    metadata={"hnsw:space": "cosine"}
)

# ── Indexación en batches ──────────────────────────────────────
print(f"⚡ Vectorizando e indexando (batch_size={BATCH_SIZE})...")

total = len(df)
for start in range(0, total, BATCH_SIZE):
    batch = df.iloc[start : start + BATCH_SIZE]

    collection.add(
        ids=batch["product_id"].astype(str).tolist(),
        documents=batch["document"].tolist(),
        metadatas=batch[[
            "category", "avg_price", "avg_rating",
            "total_orders", "positive_rate"
        ]].to_dict(orient="records"),
    )

    end = min(start + BATCH_SIZE, total)
    print(f"   [{end:>5}/{total}] indexados")

print(f"\n✅ Indexación completa — {collection.count():,} documentos en ChromaDB")
print(f"   Guardado en: {CHROMA_PATH}/")
