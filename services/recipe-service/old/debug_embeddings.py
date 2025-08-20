#!/usr/bin/env python3
"""
Debug embedding generation to find why vectors are not diverse
"""

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from qdrant_client import QdrantClient
import json

# Initialize the same model we're using
print("🔍 DEBUG: Testing embedding generation...")

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2", use_fast=False)
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model.eval()

def embed_text_debug(text):
    """Generate embedding with debugging"""
    print(f"Input text: '{text[:100]}...'")
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    print(f"Tokenized input shape: {inputs['input_ids'].shape}")
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Mean pooling
    embeddings = outputs.last_hidden_state.mean(dim=1)[0].cpu().tolist()
    
    print(f"Output embedding shape: {len(embeddings)}")
    print(f"First 5 values: {embeddings[:5]}")
    print(f"Embedding stats: min={min(embeddings):.4f}, max={max(embeddings):.4f}, mean={np.mean(embeddings):.4f}")
    print(f"Non-zero values: {sum(1 for x in embeddings if abs(x) > 0.001)}/{len(embeddings)}")
    
    return embeddings

# Test different recipe texts
test_recipes = [
    "Recipe: Chocolate Cake\nIngredients: chocolate, flour, sugar, eggs, butter",
    "Recipe: Grilled Chicken\nIngredients: chicken breast, olive oil, salt, pepper, herbs",  
    "Recipe: Caesar Salad\nIngredients: lettuce, parmesan, croutons, caesar dressing",
    "Recipe: Mango Smoothie\nIngredients: mango, yogurt, honey, ice",
    ""  # Empty text test
]

print("\n" + "="*60)
print("TESTING EMBEDDING GENERATION")
print("="*60)

embeddings_list = []
for i, recipe_text in enumerate(test_recipes):
    print(f"\n--- Test {i+1} ---")
    embedding = embed_text_debug(recipe_text)
    embeddings_list.append(embedding)

# Compare embeddings for diversity
print("\n" + "="*60)
print("EMBEDDING DIVERSITY ANALYSIS")
print("="*60)

if len(embeddings_list) >= 2:
    # Calculate cosine similarities between embeddings
    from sklearn.metrics.pairwise import cosine_similarity
    
    embeddings_array = np.array(embeddings_list)
    similarities = cosine_similarity(embeddings_array)
    
    print("Cosine similarity matrix:")
    for i, row in enumerate(similarities):
        print(f"Recipe {i+1}: {[f'{val:.3f}' for val in row]}")
    
    # Check if embeddings are too similar (indicating a problem)
    off_diagonal = similarities[np.triu_indices_from(similarities, k=1)]
    avg_similarity = np.mean(off_diagonal)
    
    print(f"\nAverage similarity between different recipes: {avg_similarity:.3f}")
    
    if avg_similarity > 0.95:
        print("🚨 PROBLEM: Embeddings are too similar! Likely all identical or near-identical.")
    elif avg_similarity < 0.3:
        print("✅ GOOD: Embeddings show good diversity")
    else:
        print("⚠️  MODERATE: Embeddings have some diversity but could be better")

# Test connection to Qdrant and check actual stored vectors
print("\n" + "="*60)
print("CHECKING QDRANT STORED VECTORS")
print("="*60)

try:
    client = QdrantClient(url="http://localhost:6333")
    collections = client.get_collections()
    
    print(f"Available collections: {[c.name for c in collections.collections]}")
    
    # Sample a few vectors from each collection
    for collection in collections.collections:
        collection_name = collection.name
        if collection_name.startswith(('desserts', 'protein', 'quick')):
            print(f"\n--- Collection: {collection_name} ---")
            
            try:
                # Get some random points
                points = client.scroll(
                    collection_name=collection_name,
                    limit=3,
                    with_vectors=True
                )
                
                if points[0]:  # If we have points
                    for i, point in enumerate(points[0][:2]):  # Check first 2
                        vector = point.vector
                        if vector:
                            print(f"Point {point.id}:")
                            print(f"  Vector length: {len(vector)}")
                            print(f"  First 5 values: {vector[:5]}")
                            print(f"  Vector stats: min={min(vector):.4f}, max={max(vector):.4f}, mean={np.mean(vector):.4f}")
                            print(f"  Non-zero values: {sum(1 for x in vector if abs(x) > 0.001)}/{len(vector)}")
                        else:
                            print(f"Point {point.id}: No vector data")
                else:
                    print("No points found in collection")
                    
            except Exception as e:
                print(f"Error accessing collection {collection_name}: {e}")
    
except Exception as e:
    print(f"Error connecting to Qdrant: {e}")

print("\n" + "="*60)
print("DIAGNOSIS COMPLETE")
print("="*60)