import os
os.environ['TRANSFORMERS_NO_TF'] = '1'

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

# === CONFIGURATION ===
CSV_PATH = "kaggleRecipes/recipes.csv"
COLLECTION_NAME = "recipes"
VECTOR_SIZE = 384  # for all-MiniLM-L6-v2 embedding model

# === LOAD EMBEDDING MODEL ===
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2", use_fast=False)
model     = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model.eval()

def embed_text(text: str):
    inputs  = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    # Mean-pool the token embeddings
    embeddings = outputs.last_hidden_state  # [1, seq_len, hidden_dim]
    return embeddings.mean(dim=1)[0].cpu().tolist()

# === CONNECT TO QDRANT ===
client = QdrantClient(url="http://localhost:6333")

# === (RE)CREATE COLLECTION ===
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=rest.VectorParams(size=VECTOR_SIZE, distance=rest.Distance.COSINE),
)

# === LOAD DATA ===
df = pd.read_csv(CSV_PATH)
df = df.dropna(subset=["recipe_name", "directions"])  # keep only entries with these

# === PROCESS AND UPLOAD RECIPES ===
for i, row in df.iterrows():
    # Prepare text to embed - include relevant fields as text
    embed_input = (
        f"Recipe: {row['recipe_name']}\n"
        f"Cook time: {row.get('cook_time', '')}\n"
        f"Total time: {row.get('total_time', '')}\n"
        f"Servings: {row.get('servings', '')}\n"
        f"Yield: {row.get('yield', '')}\n"
        f"Ingredients: {row.get('ingredients', '')}\n"
        f"Directions: {row['directions']}\n"
        f"Nutrition: {row.get('nutrition', '')}\n"
        f"Timing: {row.get('timing', '')}\n"
    )

    vector = embed_text(embed_input)

    # Prepare payload for metadata storage
    payload = {
        "recipe_name": row["recipe_name"],
        "prep_time": row.get("prep_time"),
        "cook_time": row.get("cook_time"),
        "total_time": row.get("total_time"),
        "servings": row.get("servings"),
        "yield": row.get("yield"),
        "ingredients": row.get("ingredients"),
        "directions": row.get("directions"),
        "rating": row.get("rating"),
        "url": row.get("url"),
        "cuisine_path": row.get("cuisine_path"),
        "nutrition": row.get("nutrition"),
        "timing": row.get("timing"),
        "img_src": row.get("img_src"),
    }

    point = rest.PointStruct(
        id=i,  # Use row index as unique integer ID
        vector=vector,
        payload=payload,
    )

    client.upsert(collection_name=COLLECTION_NAME, points=[point])
    print(f"✅ Uploaded: {row['recipe_name']}")

print("🎉 All recipes have been embedded and stored in Qdrant.")
