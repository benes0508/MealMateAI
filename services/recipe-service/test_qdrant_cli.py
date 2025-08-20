#!/usr/bin/env python3
"""
Interactive Qdrant Test CLI for MealMateAI Recipe Service
Test semantic search functionality across recipe collections
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

# Set environment variables before imports
os.environ['TRANSFORMERS_NO_TF'] = '1'

try:
    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as rest
    from qdrant_client.http.exceptions import ResponseHandlingException
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Please install required packages: pip install sentence-transformers qdrant-client")
    sys.exit(1)

# Configuration
QDRANT_URL = "http://localhost:6333"

# Available collections
AVAILABLE_COLLECTIONS = [
    "baked-breads",
    "quick-light", 
    "protein-mains",
    "comfort-cooked",
    "desserts-sweets",
    "breakfast-morning",
    "plant-based",
    "fresh-cold"
]

class QdrantTestCLI:
    """
    Interactive CLI for testing Qdrant vector search functionality
    """
    
    def __init__(self):
        self.client = None
        self.model = None
        self.current_collection = None
        self.collections_info = {}
        
    def initialize(self) -> bool:
        """Initialize Qdrant client and embedding model"""
        print("🚀 QDRANT RECIPE SEARCH TEST CLI")
        print("=" * 50)
        
        # Initialize Qdrant client
        print(f"🔌 Connecting to Qdrant at {QDRANT_URL}...")
        try:
            self.client = QdrantClient(url=QDRANT_URL)
            print("✅ Connected to Qdrant")
        except Exception as e:
            print(f"❌ Failed to connect to Qdrant: {e}")
            print("💡 Make sure Qdrant is running and vector database is loaded")
            return False
        
        # Load collections info
        print("📁 Loading collection information...")
        self.load_collections_info()
        
        # Initialize embedding model
        print("🤖 Loading embedding model (all-mpnet-base-v2)...")
        try:
            self.model = SentenceTransformer("all-mpnet-base-v2")
            print("✅ Embedding model loaded")
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            return False
        
        return True
    
    def load_collections_info(self):
        """Load information about available collections"""
        # First get list of all collections
        try:
            collections_list = self.client.get_collections()
            existing_collection_names = [col.name for col in collections_list.collections]
        except Exception as e:
            print(f"⚠️  Warning: Could not get collections list: {e}")
            existing_collection_names = []
        
        for collection_name in AVAILABLE_COLLECTIONS:
            if collection_name in existing_collection_names:
                # Collection exists, try to get vector count via different method
                try:
                    # Try to count vectors using scroll API
                    result = self.client.scroll(collection_name, limit=1, with_payload=False, with_vectors=False)
                    # Use a simple search to estimate collection size
                    dummy_vector = [0.0] * 768  # Zero vector for counting
                    search_result = self.client.search(
                        collection_name=collection_name,
                        query_vector=dummy_vector,
                        limit=1,
                        with_payload=False,
                        with_vectors=False
                    )
                    # If search works, collection has data
                    self.collections_info[collection_name] = {
                        "vectors_count": "loaded",  # We know it has data but exact count isn't critical
                        "status": "ready"
                    }
                except Exception as count_error:
                    # Collection exists but might be empty
                    self.collections_info[collection_name] = {
                        "vectors_count": "unknown",
                        "status": "ready"
                    }
            else:
                # Collection doesn't exist
                self.collections_info[collection_name] = {
                    "vectors_count": 0,
                    "status": "missing"
                }
    
    def display_collections(self):
        """Display available collections"""
        print("\n📁 AVAILABLE COLLECTIONS:")
        print("-" * 40)
        
        for i, collection_name in enumerate(AVAILABLE_COLLECTIONS, 1):
            info = self.collections_info.get(collection_name, {})
            count = info.get("vectors_count", 0)
            status = info.get("status", "unknown")
            
            if status == "ready":
                if isinstance(count, str):
                    print(f"   {i:2d}. {collection_name:<20} ({count}) ✅")
                else:
                    print(f"   {i:2d}. {collection_name:<20} ({count:,} recipes) ✅")
            else:
                print(f"   {i:2d}. {collection_name:<20} ({status}) ❌")
        
        print(f"   {len(AVAILABLE_COLLECTIONS)+1:2d}. all-collections      (search across all)")
        print(f"   {len(AVAILABLE_COLLECTIONS)+2:2d}. quit                 (exit CLI)")
    
    def select_collection(self) -> bool:
        """Allow user to select a collection"""
        while True:
            self.display_collections()
            
            try:
                choice = input(f"\n🎯 Select collection (1-{len(AVAILABLE_COLLECTIONS)+2}): ").strip()
                
                if not choice:
                    continue
                
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(AVAILABLE_COLLECTIONS):
                    collection_name = AVAILABLE_COLLECTIONS[choice_num - 1]
                    info = self.collections_info.get(collection_name, {})
                    
                    if info.get("status") == "ready":
                        self.current_collection = collection_name
                        print(f"✅ Selected collection: {collection_name}")
                        return True
                    else:
                        print(f"❌ Collection {collection_name} is not ready: {info.get('status')}")
                        continue
                
                elif choice_num == len(AVAILABLE_COLLECTIONS) + 1:
                    self.current_collection = "all"
                    print("✅ Selected: Search across all collections")
                    return True
                
                elif choice_num == len(AVAILABLE_COLLECTIONS) + 2:
                    print("👋 Goodbye!")
                    return False
                
                else:
                    print(f"❌ Invalid choice. Please select 1-{len(AVAILABLE_COLLECTIONS)+2}")
                    
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return False
    
    def search_recipes(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for recipes using semantic similarity"""
        print(f"🔍 Searching for: '{query}'")
        print(f"📊 Top {top_k} results from {self.current_collection}")
        
        # Generate query embedding
        try:
            query_embedding = self.model.encode(query, convert_to_tensor=False).tolist()
        except Exception as e:
            print(f"❌ Error generating query embedding: {e}")
            return []
        
        results = []
        
        if self.current_collection == "all":
            # Search across all collections
            for collection_name in AVAILABLE_COLLECTIONS:
                info = self.collections_info.get(collection_name, {})
                if info.get("status") != "ready":
                    continue
                    
                try:
                    collection_results = self.client.search(
                        collection_name=collection_name,
                        query_vector=query_embedding,
                        limit=top_k // 2,  # Fewer results per collection
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    for result in collection_results:
                        results.append({
                            "collection": collection_name,
                            "score": result.score,
                            "payload": result.payload
                        })
                        
                except Exception as e:
                    print(f"⚠️  Error searching collection {collection_name}: {e}")
            
            # Sort all results by score
            results.sort(key=lambda x: x["score"], reverse=True)
            results = results[:top_k]  # Keep only top_k overall
            
        else:
            # Search single collection
            try:
                search_results = self.client.search(
                    collection_name=self.current_collection,
                    query_vector=query_embedding,
                    limit=top_k,
                    with_payload=True,
                    with_vectors=False
                )
                
                for result in search_results:
                    results.append({
                        "collection": self.current_collection,
                        "score": result.score,
                        "payload": result.payload
                    })
                    
            except Exception as e:
                print(f"❌ Error searching collection {self.current_collection}: {e}")
                return []
        
        return results
    
    def display_results(self, results: List[Dict]):
        """Display search results in a formatted way"""
        if not results:
            print("❌ No results found")
            return
        
        print(f"\n🎯 SEARCH RESULTS ({len(results)} found):")
        print("=" * 70)
        
        for i, result in enumerate(results, 1):
            score = result["score"]
            collection = result["collection"]
            payload = result["payload"]
            
            title = payload.get("title", "Unknown Recipe")
            recipe_id = payload.get("recipe_id", "N/A")
            summary = payload.get("summary", "No summary available")
            confidence = payload.get("confidence", 0)
            
            print(f"\n{i:2d}. {title}")
            print(f"    📁 Collection: {collection}")
            print(f"    🔢 Recipe ID: {recipe_id}")
            print(f"    ⭐ Similarity: {score:.3f}")
            print(f"    🎯 Classification Confidence: {confidence}")
            print(f"    📝 Summary: {summary[:200]}...")
            
            # Show ingredient preview if available
            ingredients = payload.get("ingredients_preview", "")
            if ingredients:
                print(f"    🥗 Ingredients: {ingredients[:100]}...")
    
    def search_session(self):
        """Interactive search session"""
        print(f"\n🔍 SEARCH MODE - Collection: {self.current_collection}")
        print("💡 Enter search queries or 'menu' to change collection, 'quit' to exit")
        print("-" * 50)
        
        while True:
            try:
                query = input("\n🔍 Enter search query: ").strip()
                
                if not query:
                    continue
                
                if query.lower() == 'menu':
                    return True  # Return to collection selection
                
                if query.lower() in ['quit', 'exit', 'q']:
                    return False  # Exit completely
                
                # Get top_k from user (optional)
                try:
                    top_k_input = input("📊 Number of results (default 5): ").strip()
                    top_k = int(top_k_input) if top_k_input else 5
                    top_k = max(1, min(top_k, 20))  # Limit between 1-20
                except ValueError:
                    top_k = 5
                
                # Perform search
                start_time = time.time()
                results = self.search_recipes(query, top_k)
                search_time = time.time() - start_time
                
                # Display results
                self.display_results(results)
                
                print(f"\n⏱️  Search completed in {search_time:.2f}s")
                
            except KeyboardInterrupt:
                print("\n👋 Returning to collection menu...")
                return True
            except Exception as e:
                print(f"❌ Error during search: {e}")
    
    def run(self):
        """Main CLI loop"""
        if not self.initialize():
            return 1
        
        print("\n🎉 CLI ready! Let's test some recipe searches.")
        
        while True:
            # Collection selection
            if not self.select_collection():
                break
            
            # Search session
            continue_session = self.search_session()
            if not continue_session:
                break
        
        return 0

def main():
    """Main execution"""
    cli = QdrantTestCLI()
    return cli.run()

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        exit(0)