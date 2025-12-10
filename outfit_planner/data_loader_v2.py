import json
import os
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

class CatalogLoaderV2:
    """
    Enhanced catalog loader supporting Part 1 integration with hybrid search.
    
    Features:
    - Base Path Support: Relative paths for integration.
    - Standardized Catalog: Prefer loading catalog_standardized.json.
    - Hybrid Search: Embedding + Keyword fallback.
    """
    
    def __init__(
        self,
        base_path: str = ".",
        model_name: str = "all-MiniLM-L6-v2",
        auto_detect_model: bool = True
    ):
        """
        Initialize the catalog loader with a base directory.
        
        Args:
            base_path: Root directory containing the data files (json/npy).
            model_name: Sentence transformer model for encoding queries.
            auto_detect_model: If True, try to auto-detect compatible model.
        """
        self.base_path = base_path
        self.model_name = model_name
        self.auto_detect_model = auto_detect_model
        
        # 1. 定義檔案路徑 (相對於 base_path)
        self.embeddings_path = os.path.join(base_path, "outfit_embeddings.npy")
        self.descriptions_path = os.path.join(base_path, "outfit_descriptions.json")
        self.standardized_catalog_path = os.path.join(base_path, "catalog_standardized.json")
        
        # 2. 載入 Catalog (優先使用標準化後的資料)
        if os.path.exists(self.standardized_catalog_path):
            print(f"Info: Loading standardized catalog from {self.standardized_catalog_path}")
            self.catalog = self._load_json(self.standardized_catalog_path)
        elif os.path.exists(self.descriptions_path):
            print(f"Info: Loading raw descriptions from {self.descriptions_path}")
            self.catalog = self._load_descriptions() # Fallback logic
        else:
            raise FileNotFoundError(f"No catalog found in {base_path}. Expected catalog_standardized.json or outfit_descriptions.json")
            
        self.catalog_size = len(self.catalog)
        
        # 3. 載入 Embeddings
        self.embeddings = None
        self.embedding_model = None
        self._load_embeddings_and_model()

    def _load_json(self, path: str) -> Dict[str, Any]:
        """Generic JSON loader helper."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_descriptions(self) -> Dict[str, Dict[str, Any]]:
        """Legacy loader for outfit_descriptions.json (Part 1 raw format)."""
        with open(self.descriptions_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # If data is a list, convert to dict keyed by filename/item_id
        if isinstance(data, list):
            return {f"outfit_{i}": item for i, item in enumerate(data)}
        return data
    
    def _load_embeddings_and_model(self):
        """Load embeddings and try to initialize compatible model."""
        if not os.path.exists(self.embeddings_path):
            print(f"Info: Embeddings file not found at {self.embeddings_path}. Using keyword-only search.")
            return
        
        try:
            self.embeddings = np.load(self.embeddings_path)
            print(f"Info: Loaded embeddings shape {self.embeddings.shape}")
        except Exception as e:
            print(f"Warning: Failed to load embeddings: {e}")
            return
        
        if not HAS_SENTENCE_TRANSFORMERS:
            print("Warning: sentence-transformers not installed. Using keyword-only search.")
            return
        
        # Try to load the specified model and check compatibility
        self._try_load_model(self.model_name)
        
        # If failed and auto-detect enabled, try candidate models
        if self.embedding_model is None and self.auto_detect_model:
            self._auto_detect_model()

    # ... (以下的方法如 _try_load_model, search_by_text, filter_metadata 等保持不變)
    
    def _try_load_model(self, model_name: str) -> bool:
        """Try to load a model and verify embedding dimension compatibility."""
        try:
            model = SentenceTransformer(model_name)
            sample_emb = model.encode(["test"], convert_to_numpy=True)
            model_dim = sample_emb.shape[1]
            embeddings_dim = self.embeddings.shape[1]
            
            if model_dim == embeddings_dim:
                self.embedding_model = model
                self.model_name = model_name
                print(f"Info: Loaded model '{model_name}' (dim={model_dim})")
                return True
            else:
                print(f"Warning: Model dimension mismatch: model={model_dim}, embeddings={embeddings_dim}")
                return False
        except Exception as e:
            print(f"Warning: Failed to load model '{model_name}': {e}")
            return False
    
    def _auto_detect_model(self):
        """Try to auto-detect a compatible model from common options."""
        candidates = [
            'distiluse-base-multilingual-cased-v2',  # 512-dim (Matches typical CLIP-like usage in sentence-transformers)
            'sentence-transformers/distiluse-base-multilingual-cased-v2',
            'all-MiniLM-L6-v2', # 384-dim
            'paraphrase-multilingual-MiniLM-L12-v2',  # 384-dim
            'paraphrase-xlm-r-multilingual-v1',  # 768-dim
            'all-mpnet-base-v2',  # 768-dim
            'clip-ViT-B-32', # If using CLIP specific models
        ]
        
        embeddings_dim = self.embeddings.shape[1]
        print(f"Info: Auto-detecting compatible model for {embeddings_dim}-dim embeddings...")
        
        for model_name in candidates:
            if self._try_load_model(model_name):
                return
        
        print(f"Info: No compatible model auto-detected. Using keyword-only search.")

    def search_by_text(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search catalog using hybrid approach: embedding-based + keyword fallback.
        """
        if self.embedding_model is not None and self.embeddings is not None:
            return self._search_by_embedding(query, top_k, threshold)
        else:
            return self._search_by_keyword(query, top_k)
    
    def _search_by_embedding(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Semantic search using embeddings."""
        # Encode query
        query_emb = self.embedding_model.encode([query], convert_to_numpy=True)
        query_emb = query_emb / (np.linalg.norm(query_emb, axis=1, keepdims=True) + 1e-10)
        
        # Normalize embeddings for cosine similarity
        embeddings_norm = self.embeddings / (np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-10)
        
        # Compute similarities
        similarities = np.dot(embeddings_norm, query_emb.T).flatten()
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        catalog_items = list(self.catalog.items())
        
        # Handle case where catalog size doesn't match embeddings size
        max_idx = min(len(catalog_items), len(self.embeddings))
        
        for idx in top_indices:
            if idx >= max_idx: continue
            
            score = float(similarities[idx])
            if score >= threshold:
                # catalog_items is list of (key, value)
                item_key, item_meta = catalog_items[int(idx)]
                results.append((item_meta, score))
        
        return results
    
    def _search_by_keyword(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Keyword-based fallback search."""
        keywords = query.lower().split()
        results = []
        
        for item_key, item_meta in self.catalog.items():
            score = 0
            # Construct searchable text from metadata fields
            text_to_search = (
                str(item_meta.get("complete_description", "")).lower() + " " +
                str(item_meta.get("description", "")).lower() + " " + # Added generic description field
                str(item_meta.get("color_primary", "")).lower() + " " +
                str(item_meta.get("material", "")).lower() + " " +
                str(item_meta.get("category", "")).lower()
            )
            
            for keyword in keywords:
                if keyword in text_to_search:
                    score += 1
            
            if score > 0:
                normalized_score = min(score / len(keywords), 1.0) if keywords else 0.0
                results.append((item_meta, normalized_score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def filter_metadata(
        self,
        context: Dict[str, Any],
        candidates: List[Tuple[Dict[str, Any], float]]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Apply hard metadata filtering rules."""
        if not candidates:
            return candidates

        weather = context.get("weather", {})
        # Handle string like "28°C" or int 28
        temp_raw = weather.get("temperature", None)
        temp = None
        if isinstance(temp_raw, (int, float)):
            temp = temp_raw
        elif isinstance(temp_raw, str) and "°" in temp_raw:
            try:
                temp = float(temp_raw.split("°")[0])
            except:
                pass
        
        occasion = context.get("occasion", {})
        # Occasion might be string or dict
        occ_text = str(occasion).lower() if not isinstance(occasion, dict) else str(occasion.get("type", "")).lower()

        filtered = []

        for item, score in candidates:
            cat = str(item.get("category", "")).lower()
            material = str(item.get("material", "")).lower()
            desc = str(item.get("description", "")).lower()

            # 1. Swimming Rule
            if "swim" in occ_text or "beach" in occ_text:
                # If specifically swimming, prioritize swimwear
                if "swim" in occ_text and cat not in ["swimwear", "swimsuit", "bikini"]:
                     # Only skip if we are strict, for now let's just allow it but maybe logic handles it
                     pass

            # 2. Temperature Rule (> 28°C)
            if temp is not None and temp > 28:
                if "wool" in material or "thick" in desc or cat in ["coat", "parka", "heavy jacket"]:
                    continue

            filtered.append((item, score))

        return filtered if filtered else candidates

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self.catalog.values())
        
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_items": self.catalog_size,
            "base_path": self.base_path,
            "has_embeddings": self.embeddings is not None
        }

# Backward compatibility
CatalogLoader = CatalogLoaderV2

if __name__ == "__main__":
    # Test
    loader = CatalogLoaderV2(base_path=".")
    print(f"Loaded {loader.catalog_size} items from {loader.base_path}")