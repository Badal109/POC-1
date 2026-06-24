import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer
from tools.snowflake_metadata import fetch_all_metadata

MODEL = SentenceTransformer("all-MiniLM-L6-v2")
CHROMA_CLIENT = chromadb.PersistentClient(path=".chroma_db")
COLLECTION_NAME = "retail_db_columns"

def build_vector_index():
    """Embed all column names from RETAIL_DB and store in chromadb."""
    meta = fetch_all_metadata()
    collection = CHROMA_CLIENT.get_or_create_collection(COLLECTION_NAME)

    docs, ids, metadatas = [], [], []
    for layer, tables in meta.items():
        for table, cols in tables.items():
            for col in cols:
                doc_id = f"{layer}__{table}__{col}"
                # Natural language representation for better embedding
                text = f"{col.replace('_', ' ').lower()} in {table.replace('_', ' ').lower()} {layer.lower()} layer"
                docs.append(text)
                ids.append(doc_id)
                metadatas.append({
                    "layer": layer,
                    "table": table,
                    "column": col
                })

    collection.upsert(documents=docs, ids=ids, metadatas=metadatas)
    print(f"Indexed {len(docs)} columns into chromadb")
    return len(docs)

def semantic_search(field: str, top_k: int = 3, threshold: float = 0.35) -> list:
    """
    Search for best matching columns semantically.
    Returns list of matches with layer, table, column, similarity score.
    """
    try:
        collection = CHROMA_CLIENT.get_collection(COLLECTION_NAME)
    except Exception:
        build_vector_index()
        collection = CHROMA_CLIENT.get_collection(COLLECTION_NAME)

    query_text = field.replace("_", " ").lower()
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k,
        include=["metadatas", "distances"]
    )

    matches = []
    for i, meta in enumerate(results["metadatas"][0]):
        # chromadb returns L2 distance — convert to similarity
        distance = results["distances"][0][i]
        similarity = max(0, 1 - (distance / 2))
        if similarity >= threshold:
            matches.append({
                "column": meta["column"],
                "table": meta["table"],
                "layer": meta["layer"],
                "similarity": round(similarity, 3)
            })

    # Sort by layer priority (GOLD > SILVER > BRONZE) then similarity
    layer_priority = {"GOLD": 0, "SILVER": 1, "BRONZE": 2}
    matches.sort(key=lambda x: (layer_priority.get(x["layer"], 3), -x["similarity"]))
    return matches

if __name__ == "__main__":
    print("Building vector index...")
    build_vector_index()
    # Test
    tests = ["promotional expenditure", "revenue", "store footprint", "market share"]
    for t in tests:
        results = semantic_search(t)
        print(f"\n'{t}':")
        for r in results:
            print(f"  {r['layer']}.{r['table']}.{r['column']} — {r['similarity']}")