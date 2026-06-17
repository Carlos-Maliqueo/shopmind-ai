"""
Módulo RAG — Retrieval desde ChromaDB
"""

import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "chroma_db"
COLLECTION  = "products"
MODEL_NAME  = "all-MiniLM-L6-v2"


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=MODEL_NAME
    )
    return client.get_collection(name=COLLECTION, embedding_function=ef)


def search_products(query: str, n_results: int = 5) -> list[dict]:
    """
    Busca productos similares a la query en el vector store.
    Retorna lista de dicts con document + metadata.
    """
    collection = get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    output = []
    for i in range(len(results["ids"][0])):
        output.append({
            "product_id": results["ids"][0][i],
            "document":   results["documents"][0][i],
            "metadata":   results["metadatas"][0][i],
            "distance":   results["distances"][0][i],
        })
    return output


if __name__ == "__main__":
    # Test rápido
    query = "headphones electronics"
    print(f"🔍 Query: '{query}'\n")
    results = search_products(query, n_results=3)
    for r in results:
        print(f"  [{r['metadata']['category']}] rating={r['metadata']['avg_rating']} price=${r['metadata']['avg_price']}")
        print(f"  {r['document'][:120]}...")
        print()
