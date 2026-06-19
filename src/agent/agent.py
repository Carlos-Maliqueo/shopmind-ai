"""
Fase 3 — Agente ShopMind AI con tool calling usando Gemini
"""

import os
import json
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from src.rag.retriever import search_products

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ── Datos para análisis pandas ─────────────────────────────────
_df = None

def _get_df() -> pd.DataFrame:
    global _df
    if _df is None:
        _df = pd.read_csv("data/processed/product_summary.csv")
    return _df


# ── Herramientas del agente ────────────────────────────────────

def tool_search_products(query: str, n_results: int = 5) -> str:
    """Busca productos en el vector store por similitud semántica."""
    results = search_products(query, n_results=int(n_results))
    if not results:
        return "No se encontraron productos relevantes."

    lines = []
    for r in results:
        m = r["metadata"]
        category   = m.get("category", "N/A")
        avg_price  = m.get("avg_price", "N/A")
        avg_rating = m.get("avg_rating", "N/A")
        total_orders = m.get("total_orders", "N/A")
        positive_rate = m.get("positive_rate")
        positive_pct = f"{int(positive_rate*100)}%" if positive_rate is not None else "N/A"
        lines.append(
            f"- Categoría: {category} | "
            f"Precio promedio: ${avg_price} | "
            f"Rating: {avg_rating}/5 | "
            f"Pedidos: {total_orders} | "
            f"% positivos: {positive_pct}"
        )
    return "\n".join(lines)


def tool_analyze_category(category: str) -> str:
    """Retorna métricas agregadas de una categoría específica."""
    df = _get_df()
    subset = df[df["category"].str.contains(category, case=False, na=False)]

    if subset.empty:
        # Sugerir categorías parecidas usando matching simple de palabras
        import difflib
        all_categories = df["category"].dropna().unique().tolist()
        suggestions = difflib.get_close_matches(category, all_categories, n=5, cutoff=0.3)
        if suggestions:
            return (
                f"No se encontró la categoría '{category}'. "
                f"Categorías similares disponibles: {', '.join(suggestions)}"
            )
        return (
            f"No se encontró la categoría '{category}'. "
            f"Usa la herramienta list_categories para ver todas las categorías disponibles."
        )

    stats = {
        "categoria":         category,
        "total_productos":   int(len(subset)),
        "precio_promedio":   round(float(subset["avg_price"].mean()), 2),
        "rating_promedio":   round(float(subset["avg_rating"].mean()), 2),
        "total_pedidos":     int(subset["total_orders"].sum()),
        "tasa_positiva_pct": round(float(subset["positive_rate"].mean()) * 100, 1),
        "precio_min":        round(float(subset["avg_price"].min()), 2),
        "precio_max":        round(float(subset["avg_price"].max()), 2),
    }
    return json.dumps(stats, ensure_ascii=False, indent=2)


def tool_list_categories() -> str:
    """Lista todas las categorías de productos disponibles en el dataset."""
    df = _get_df()
    categories = sorted(df["category"].dropna().unique().tolist())
    return f"Categorías disponibles ({len(categories)}):\n" + ", ".join(categories)


# ── Definición de tools para Gemini ───────────────────────────

search_products_tool = genai.protos.Tool(
    function_declarations=[
        genai.protos.FunctionDeclaration(
            name="search_products",
            description=(
                "Busca productos en la base vectorial usando similitud semántica. "
                "Úsala cuando el usuario pregunte por recomendaciones, productos similares "
                "o quiera encontrar ítems por descripción o categoría."
            ),
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "query": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="Descripción del producto o categoría a buscar"
                    ),
                    "n_results": genai.protos.Schema(
                        type=genai.protos.Type.INTEGER,
                        description="Cantidad de resultados a retornar (default: 5)"
                    ),
                },
                required=["query"]
            )
        )
    ]
)

analyze_category_tool = genai.protos.Tool(
    function_declarations=[
        genai.protos.FunctionDeclaration(
            name="analyze_category",
            description=(
                "Retorna métricas estadísticas de una categoría: precio promedio, rating, "
                "total de pedidos, tasa de reviews positivas. Úsala cuando el usuario pregunte "
                "por el desempeño o estadísticas de una categoría."
            ),
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "category": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="Nombre o parte del nombre de la categoría a analizar"
                    ),
                },
                required=["category"]
            )
        )
    ]
)

list_categories_tool = genai.protos.Tool(
    function_declarations=[
        genai.protos.FunctionDeclaration(
            name="list_categories",
            description=(
                "Lista todas las categorías de productos disponibles en el dataset. "
                "Úsala cuando no encuentres una categoría que el usuario mencionó, "
                "o cuando el usuario pregunte qué categorías existen."
            ),
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={}
            )
        )
    ]
)

TOOLS = [search_products_tool, analyze_category_tool, list_categories_tool]

TOOL_MAP = {
    "search_products":  tool_search_products,
    "analyze_category": tool_analyze_category,
    "list_categories":  tool_list_categories,
}


# ── System prompt ──────────────────────────────────────────────

def _load_system_prompt() -> str:
    path = "prompts/agent_system.md"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Eres ShopMind AI, un asistente experto en análisis de e-commerce."


# ── Agente: agentic loop ───────────────────────────────────────

class ShopMindAgent:
    def __init__(self):
        system_prompt = _load_system_prompt()
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            tools=TOOLS,
            system_instruction=system_prompt,
        )

    def run(self, user_message: str) -> str:
        chat = self.model.start_chat(enable_automatic_function_calling=False)
        response = chat.send_message(user_message)

        while True:
            fn_calls = []
            for part in response.parts:
                if hasattr(part, "function_call") and part.function_call.name:
                    fn_calls.append(part.function_call)

            if not fn_calls:
                return response.text

            tool_results = []
            for fn_call in fn_calls:
                name = fn_call.name
                args = dict(fn_call.args)
                print(f"  🔧 Usando herramienta: {name}({args})")

                fn     = TOOL_MAP.get(name)
                result = fn(**args) if fn else f"Herramienta '{name}' no encontrada."

                tool_results.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=name,
                            response={"result": result}
                        )
                    )
                )

            response = chat.send_message(tool_results)


# ── CLI interactivo ────────────────────────────────────────────

if __name__ == "__main__":
    agent = ShopMindAgent()
    print("🛒 ShopMind AI — Agente RAG de Recomendación (Gemini)")
    print("   Escribe 'salir' para terminar\n")

    while True:
        user_input = input("Tú: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("salir", "exit", "quit"):
            print("¡Hasta luego!")
            break

        print()  # línea en blanco antes de procesar
        answer = agent.run(user_input)
        print(f"Agente: {answer}\n")
        print()
