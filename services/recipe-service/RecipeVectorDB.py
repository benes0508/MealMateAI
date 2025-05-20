import os
import json
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from sentence_transformers import SentenceTransformer

# === CONFIGURATION ===
RECIPE_FOLDER = "recipes"  # <-- CHANGE THIS to your local path
COLLECTION_NAME = "recipes"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2

# === LOAD EMBEDDING MODEL ===
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# === CONNECT TO QDRANT ===
client = QdrantClient(url="http://localhost:6333")

# === CREATE/RESET COLLECTION ===
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=rest.VectorParams(size=VECTOR_SIZE, distance=rest.Distance.COSINE),
)

# === PROCESS RECIPE FILES ===
for filename in os.listdir(RECIPE_FOLDER):
    if not filename.endswith(".json"):
        continue

    base_name = filename[:-5]  # Remove '.json'
    json_path = os.path.join(RECIPE_FOLDER, f"{base_name}.json")
    txt_path = os.path.join(RECIPE_FOLDER, f"{base_name}.txt")

    if not os.path.exists(txt_path):
        print(f"⚠️ Skipping {base_name}: Missing .txt file.")
        continue

    # Load JSON (metadata)
    with open(json_path, "r", encoding="utf-8") as jf:
        try:
            meta = json.load(jf)[0]  # JSON file should contain a list with one recipe
        except Exception as e:
            print(f"❌ Error reading {json_path}: {e}")
            continue

    # Load TXT (instructions)
    with open(txt_path, "r", encoding="utf-8") as tf:
        instructions = tf.read()

    # Build embedding input text
    embed_text = (
        f"Title: {meta['title']}\n"
        f"Ingredients: {', '.join(i['item'] for i in meta['ingredients'])}\n\n"
        f"Instructions:\n{instructions}"
    )

    # Generate vector
    vector = model.encode(embed_text).tolist()

    # Build payload
    payload = {
        "title": meta["title"],
        "ingredients": [i["item"] for i in meta["ingredients"]],
        "allergens": meta.get("allergens", []),
        "cuisine": meta.get("cuisine", ""),
        "tags": meta.get("tags", []),
    }

    # Create point with UUID as ID
    point = rest.PointStruct(
        id=str(uuid.uuid4()),
        vector=vector,
        payload=payload,
    )

    # Upload to Qdrant
    client.upsert(collection_name=COLLECTION_NAME, points=[point])
    print(f"✅ Uploaded: {meta['title']}")

print("🎉 All available recipes have been indexed in Qdrant.")