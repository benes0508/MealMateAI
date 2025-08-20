#!/usr/bin/env python3
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    SearchParams,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
)
from pprint import pprint

# === CONFIGURATION ===
COLLECTION_NAME      = "recipes"
QDRANT_URL           = "http://localhost:6333"
EMBEDDING_MODEL_NAME = "sentence-transformers/multi-qa-mpnet-base-dot-v1"
TOP_K                = 5
HNSW_EF              = 128  # bump recall if needed

def parse_filters(filter_str: str):
    """
    Parses "field1=val1,val2; field2=val3" into FieldCondition list.
    """
    conds = []
    for part in filter_str.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        field, vals = part.split("=", 1)
        values = [v.strip() for v in vals.split(",") if v.strip()]
        if len(values) == 1:
            conds.append(
                FieldCondition(key=field.strip(), match=MatchValue(value=values[0]))
            )
        elif values:
            conds.append(
                FieldCondition(key=field.strip(), match=MatchAny(any=values))
            )
    return conds

def main():
    # 1) Load embedding model
    print("🔄 Loading multi-qa-mpnet-base-dot-v1 model...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # 2) Connect to Qdrant
    print("🔌 Connecting to Qdrant...")
    client = QdrantClient(url=QDRANT_URL)

    print("\n✅ Ready! Enter a query and optional filters (or 'exit').\n")

    try:
        while True:
            query = input("📝 Query> ").strip()
            if not query or query.lower() in ("exit", "quit"):
                print("👋 Goodbye!")
                break

            filt_in    = input("⚙️  Filters> ").strip()
            conditions = parse_filters(filt_in)
            q_filter   = Filter(must=conditions) if conditions else None

            # 3) Encode & search
            vec = model.encode(query).tolist()
            results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=vec,
                limit=TOP_K,
                search_params=SearchParams(hnsw_ef=HNSW_EF),
                query_filter=q_filter,
                with_payload=True,
            )

            # 4) Display
            print("\n🔍 Top matches:\n")
            if not results:
                print("❌ No recipes found.")
            else:
                for i, hit in enumerate(results, start=1):
                    title = hit.payload.get("title", "Untitled")
                    print(f"{i}. 🥘 {title} (score: {hit.score:.4f})")
                    pprint(hit.payload)
                    print("-" * 50)
            print()
    except KeyboardInterrupt:
        print("\n👋 Interrupted, exiting.")

if __name__ == "__main__":
    main()