#!/usr/bin/env python3
import sys
import traceback
from qdrant_client import QdrantClient
from qdrant_client.http import models
import requests
from qdrant_client.http.exceptions import ResponseHandlingException

from typing import List
from sentence_transformers import SentenceTransformer

# Initialize embedding model once
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_query(text: str) -> List[float]:
    """
    Generate embedding vector for a text query using MiniLM.
    """
    return embed_model.encode(text, show_progress_bar=False).tolist()

def main():
    # 1) Connect to Qdrant on localhost:6333
    client = QdrantClient(host="localhost", port=6333)

    # 2) List all collections
    resp = client.get_collections()
    names = [col.name for col in resp.collections]
    if not names:
        print("❗ No collections found.")
        return

    print(f"Found {len(names)} collections:\n" + "\n".join(f" - {n}" for n in names))
    print("\nTesting each collection:\n" + "-"*40)

    for name in names:
        print(f"\nCollection: {name}")
        try:
            try:
                info = client.get_collection(collection_name=name)
                vec_params: models.VectorParams = info.vectors
                size = vec_params.size
                distance = vec_params.distance.value

                cnt = client.count(collection_name=name)
                points_count = cnt.count

            except ResponseHandlingException:
                # Fallback to raw HTTP endpoint when client schema mismatch occurs
                resp = requests.get(f"http://localhost:6333/collections/{name}")
                resp.raise_for_status()
                data = resp.json().get("result", {})

                params = data["config"]["params"]["vectors"]
                size = params["size"]
                distance = params["distance"]

                # points_count key may vary by server version
                points_count = data.get("points_count", data.get("vectors_count", 0))

            print(f" • Vector size: {size}")
            print(f" • Distance:    {distance}")
            print(f" • Point count: {points_count}")

            # 5) Test a dummy search
            zero_vec = [0.0] * size
            res = client.search(
                collection_name=name,
                query_vector=zero_vec,
                limit=1,
            )
            print(f" • Search OK, returned {len(res)} result(s).")

        except Exception:
            print("❌ Error testing this collection:")
            traceback.print_exc(file=sys.stdout)

    # Extended query tests
    common_queries = ["chocolate cake", "vegetable soup"]
    per_collection_queries = {
        "quick-light": ["avocado toast", "smoothie bowl"],
        "baked-breads": ["banana bread", "bagel"],
        "fresh-cold": ["fruit salad", "gazpacho"],
        "breakfast-morning": ["pancakes", "omelette"],
        "desserts-sweets": ["cheesecake", "brownies"],
        "comfort-cooked": ["mac and cheese", "beef stew"],
        "protein-mains": ["grilled chicken", "tofu stir fry"],
        "plant-based": ["vegan curry", "lentil soup"],
    }

    results_file = "test_qdrant_query_results.txt"
    with open(results_file, "w") as f:
        f.write("=== Common queries across collections ===\n")
        for q in common_queries:
            f.write(f"\nQuery: {q}\n")
            vec = embed_query(q)
            for col in names:
                f.write(f" Collection: {col}\n")
                res = client.search(collection_name=col, query_vector=vec, limit=10)
                f.write("  Top results:\n")
                for pt in res:
                    title = pt.payload.get("name", pt.payload.get("title", str(pt.id)))
                    f.write(f"    - {title}\n")

        f.write("\n=== Per-collection multiple queries ===\n")
        for col, queries in per_collection_queries.items():
            f.write(f"\nCollection: {col}\n")
            for q in queries:
                f.write(f" Query: {q}\n")
                vec = embed_query(q)
                res = client.search(collection_name=col, query_vector=vec, limit=10)
                f.write("  Top results:\n")
                for pt in res:
                    title = pt.payload.get("name", pt.payload.get("title", str(pt.id)))
                    f.write(f"    - {title}\n")

    print(f"\nQuery test results written to {results_file}")

if __name__ == "__main__":
    main()