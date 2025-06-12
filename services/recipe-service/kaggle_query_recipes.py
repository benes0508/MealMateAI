#!/usr/bin/env python3
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import SearchParams
from pprint import pprint

# === CONFIGURATION ===
COLLECTION_NAME      = "recipes"
QDRANT_URL           = "http://localhost:6333"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K                = 5

def main():
    print("🔄 Loading model...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print("🔌 Connecting to Qdrant...")
    client = QdrantClient(url=QDRANT_URL)

    print("\n✅ Ready! Enter a query (or 'exit').\n")

    try:
        while True:
            query = input("📝 Query> ").strip()
            if not query or query.lower() in ("exit", "quit"):
                print("👋 Goodbye!")
                break

            vec = model.encode(query).tolist()
            results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=vec,
                limit=TOP_K,
                search_params=SearchParams(hnsw_ef=128),
                with_payload=True,
            )

            print("\n🔍 Top matches:\n")
            if not results:
                print("❌ No recipes found.")
            else:
                for i, hit in enumerate(results, start=1):
                    title = hit.payload.get("recipe_name") or hit.payload.get("title") or "Untitled"
                    print(f"{i}. 🥘 {title} (score: {hit.score:.4f})")
                    pprint(hit.payload)
                    print("-" * 50)
            print()

    except KeyboardInterrupt:
        print("\n👋 Interrupted, exiting.")

if __name__ == "__main__":
    main()
