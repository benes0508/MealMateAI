#!/usr/bin/env python3
import torch
from transformers import AutoTokenizer, AutoModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import SearchParams
from pprint import pprint
import argparse
import os

# === CONFIGURATION ===
COLLECTION_NAME      = "recipes"
QDRANT_URL           = "http://localhost:6333"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K                = 5

# === LOAD EMBEDDING MODEL ===
tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME, use_fast=False)
model = AutoModel.from_pretrained(EMBEDDING_MODEL_NAME)
model.eval()

def embed_text(text: str):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state  # [1, seq_len, hidden_dim]
    return embeddings.mean(dim=1)[0].cpu().tolist()

def main():
    print("🔄 Loading model...")
    # Model is already loaded above

    print("🔌 Connecting to Qdrant...")
    client = QdrantClient(url=QDRANT_URL)

    print("\n✅ Ready! Enter a query (or 'exit').\n")

    try:
        while True:
            query = input("📝 Query> ").strip()
            if not query or query.lower() in ("exit", "quit"):
                print("👋 Goodbye!")
                break

            vec = embed_text(query)
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
    parser = argparse.ArgumentParser(description="Query Qdrant with various prompts and models")
    parser.add_argument("--prompts_file", type=str, help="Path to newline-separated prompts file")
    parser.add_argument("--models_file", type=str, help="Path to newline-separated embedding model names")
    parser.add_argument("--output_dir", type=str, default="test_results", help="Directory to save results")
    args = parser.parse_args()

    # If prompts_file and models_file provided, run batch test
    if args.prompts_file and args.models_file:
        os.makedirs(args.output_dir, exist_ok=True)
        # Read prompts
        with open(args.prompts_file, "r", encoding="utf-8") as pf:
            prompts = [line.strip() for line in pf if line.strip()]
        # Read models
        with open(args.models_file, "r", encoding="utf-8") as mf:
            models = [line.strip() for line in mf if line.strip()]
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import SearchParams

        for model_name in models:
            # load model
            tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
            model = AutoModel.from_pretrained(model_name)
            model.eval()
            def embed_text_dyn(text: str):
                inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
                with torch.no_grad():
                    outputs = model(**inputs)
                return outputs.last_hidden_state.mean(dim=1)[0].cpu().tolist()

            # prepare output file
            safe_name = model_name.replace("/", "_")
            out_path = os.path.join(args.output_dir, f"results_{safe_name}.txt")
            with open(out_path, "w", encoding="utf-8") as out:
                out.write(f"Results for model: {model_name}\n\n")
                for prompt in prompts:
                    out.write(f"Prompt: {prompt}\n")
                    vec = embed_text_dyn(prompt)
                    client = QdrantClient(url=QDRANT_URL)
                    results = client.search(
                        collection_name=COLLECTION_NAME,
                        query_vector=vec,
                        limit=TOP_K,
                        search_params=SearchParams(hnsw_ef=128),
                        with_payload=True,
                    )
                    if not results:
                        out.write("  No recipes found.\n\n")
                    else:
                        for i, hit in enumerate(results, 1):
                            title = hit.payload.get("recipe_name") or hit.payload.get("title") or "Untitled"
                            out.write(f"  {i}. {title} (score: {hit.score:.4f})\n")
                        out.write("\n")
        exit(0)
    # otherwise, fall back to interactive
    main()
