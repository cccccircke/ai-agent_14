"""
Enhanced Recommendation Engine (Part 3 Core Logic) - Modified for Tone-on-Tone Composition
Implements Retrieve-Think-Generate chain for outfit recommendations.

Architecture:
1. RETRIEVE: Search catalog using hybrid search
2. THINK: Reason about candidates based on user context, weather, personal color
3. GENERATE: Create recommendation with VTON prompt for Part 4

Output format optimized for Part 4 (Virtual Try-On Presenter)
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

from src.data_loader_v2 import CatalogLoaderV2
from src.mock_context_v2 import select_context, validate_context


@dataclass
class RecommendationOutput:
    """Output schema for Part 4 (Virtual Try-On Presenter)."""
    task_id: str
    selected_outfit: Dict[str, Any]  # filename, category, description
    reasoning_log: str  # Why this outfit was chosen (Traditional Chinese)
    vton_generation_prompt: str  # For Stable Diffusion / image generation
    alternative_candidates: List[Dict[str, Any]] = None  # Top 3 alternatives
    confidence_score: float = 0.0
    generated_at: str = ""
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class OutfitRecommenderV2:
    """
    Enhanced outfit recommender with Retrieve-Think-Generate chain.
    Integrates Part 1 (Catalog) → Part 3 (Logic) → Part 4 (VTON)
    """
    
    def __init__(
        self,
        descriptions_path: str = "src/outfit_descriptions.json",
        embeddings_path: str = "src/outfit_embeddings.npy",
        model_name: str = "all-MiniLM-L6-v2",
        auto_detect_model: bool = True
    ):
        self.catalog_loader = CatalogLoaderV2(
            descriptions_path=descriptions_path,
            embeddings_path=embeddings_path,
            model_name=model_name,
            auto_detect_model=auto_detect_model
        )
    
    def recommend(
        self,
        context: Optional[Dict[str, Any]] = None,
        scenario: str = "beach_wedding",
        top_k: int = 5
    ) -> RecommendationOutput:
        """
        Generate outfit recommendation.
        Enforces: One-piece Dress OR Top + Bottom (Tone-on-Tone preference).
        """
        # 1. RETRIEVE: Load context
        if context is None:
            context = select_context(scenario)
        
        if not validate_context(context):
            raise ValueError("Invalid context: missing required fields")
        
        # 2. RETRIEVE: Get candidate outfits via hybrid search
        candidates = self._retrieve_candidates(context, top_k)

        # Hard metadata filtering
        try:
            candidates = self.catalog_loader.filter_metadata(context, candidates)
        except Exception:
            pass
        
        if not candidates:
            return self._create_empty_output(context)
        
        # 3. THINK: Score and select the "Anchor" item (Best Item)
        anchor_item, score = self._think_and_select(context, candidates)
        anchor_type = self._get_broad_category(anchor_item)

        # 3.5 COMPOSITION LOGIC (Logic Update)
        composed_pair = None
        selected_item = anchor_item # Default to anchor

        if anchor_type == "Dress":
            # If anchor is a Dress/Suit, use it directly.
            selected_item = anchor_item
            
        elif anchor_type == "Upper":
            # If anchor is Top, find matching Bottom (Tone-on-Tone)
            matching_bottom = self._find_pair_component(anchor_item, target_type="Lower")
            if matching_bottom:
                composed_pair = {"top": anchor_item, "bottom": matching_bottom}
            else:
                # Fallback: keep searching or return anchor (though single top is bad for VTON)
                pass 

        elif anchor_type == "Lower":
            # If anchor is Bottom, find matching Top (Tone-on-Tone)
            matching_top = self._find_pair_component(anchor_item, target_type="Upper")
            if matching_top:
                composed_pair = {"top": matching_top, "bottom": anchor_item}
            else:
                pass

        # 4. GENERATE: Create reasoning and VTON prompt
        if composed_pair:
            reasoning = self._generate_reasoning(context, composed_pair["top"]) + (
                f"\n搭配建議：選擇同色系/協調色調的下身 {composed_pair['bottom'].get('color_primary', '')} {composed_pair['bottom'].get('category', '')}，打造修長視覺效果。"
            )
            vton_prompt = self._generate_vton_prompt_for_pair(context, composed_pair["top"], composed_pair["bottom"])
            
            # Update selected item display for Output
            selected_outfit_dict = {
                "filename": f"{self._extract_filename(composed_pair['top'])} + {self._extract_filename(composed_pair['bottom'])}",
                "category": "Set (Top + Bottom)",
                "color": f"{composed_pair['top'].get('color_primary', '')}", # Emphasize main color
                "material": f"{composed_pair['top'].get('material', '')}",
                "description": f"Top: {composed_pair['top'].get('category')} / Bottom: {composed_pair['bottom'].get('category')}",
                "components": {
                    "top": composed_pair["top"],
                    "bottom": composed_pair["bottom"]
                }
            }
        else:
            # Single item (Dress)
            reasoning = self._generate_reasoning(context, selected_item)
            vton_prompt = self._generate_vton_prompt(context, selected_item)
            selected_outfit_dict = {
                "filename": self._extract_filename(selected_item),
                "category": selected_item.get("category", ""),
                "color": selected_item.get("color_primary", ""),
                "material": selected_item.get("material", ""),
                "description": selected_item.get("complete_description", "")
            }
        
        output = RecommendationOutput(
            task_id=f"recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            selected_outfit=selected_outfit_dict,
            reasoning_log=reasoning,
            vton_generation_prompt=vton_prompt,
            alternative_candidates=[
                {
                    "filename": self._extract_filename(c),
                    "category": c.get("category", ""),
                    "description": c.get("complete_description", "")[:100]
                }
                for c in [item for item, _ in candidates[1:4]]
            ],
            confidence_score=float(score),
            generated_at=datetime.now().isoformat()
        )
        
        return output

    def _get_broad_category(self, item: Dict[str, Any]) -> str:
        """Helper: Classify item into Upper, Lower, or Dress."""
        cat = (item.get("category", "") or "").lower()
        sub = (item.get("subcategory", "") or "").lower()
        desc = (item.get("complete_description", "") or "").lower()
        full_text = f"{cat} {sub} {desc}"
        
        # Priority: Dress/Full body
        if any(w in full_text for w in ["dress", "gown", "jumpsuit", "suit", "one-piece", "full body"]):
            return "Dress"
        
        # Lower body
        if any(w in full_text for w in ["pant", "jean", "skirt", "short", "trouser", "legging", "bottom", "kilt"]):
            return "Lower"
            
        # Upper body (Default if mostly top keywords appear)
        return "Upper"

    def _find_pair_component(self, anchor_item: Dict[str, Any], target_type: str) -> Optional[Dict[str, Any]]:
        """
        Find a matching component (Top or Bottom) prioritizing Tone-on-Tone (Same Color Family).
        
        Args:
            anchor_item: The item already selected.
            target_type: "Upper" or "Lower".
        """
        anchor_color = (anchor_item.get("color_primary", "") or "").lower()
        
        # 1. Search Query: "Color + Target Category" (e.g., "Blue Lower", "White Upper")
        # We map "Upper"/"Lower" to more searchable terms
        target_keywords = "pants skirt shorts" if target_type == "Lower" else "top shirt blouse"
        search_query = f"{anchor_color} {target_keywords}"
        
        # Retrieve candidates
        candidates = self.catalog_loader.search_by_text(query=search_query, top_k=10)
        
        best_match = None
        best_score = -1.0
        
        for item, retrieval_score in candidates:
            # Filter: Must match target category type
            if self._get_broad_category(item) != target_type:
                continue
            
            match_score = retrieval_score
            item_color = (item.get("color_primary", "") or "").lower()
            
            # Tone-on-Tone Logic: Boost score if colors are similar
            if anchor_color in item_color or item_color in anchor_color:
                match_score += 0.5  # Strong boost for same color family
            elif any(c in item_color for c in ["white", "black", "gray", "beige"]):
                match_score += 0.1  # Slight boost for neutrals if exact match not found
            else:
                match_score -= 0.2  # Penalize clashing colors
            
            if match_score > best_score:
                best_score = match_score
                best_match = item
        
        return best_match

    # --- Standard Retrieval & Reasoning Logic (Preserved) ---

    def _retrieve_candidates(self, context: Dict[str, Any], top_k: int = 5) -> List[tuple]:
        query_parts = []
        if "user_query" in context:
            query_parts.append(context["user_query"])
        
        weather = context.get("weather", {})
        temp = weather.get("temperature_c", 20)
        if temp > 28: query_parts.append("lightweight breathable cool")
        elif temp < 15: query_parts.append("warm cozy")
        
        user_profile = context.get("user_profile", {})
        if "style_preferences" in user_profile:
            query_parts.extend(user_profile["style_preferences"])
        if "personal_color" in user_profile:
            query_parts.append(user_profile["personal_color"])
            
        search_query = " ".join(query_parts)
        return self.catalog_loader.search_by_text(query=search_query, top_k=top_k, threshold=0.0)
    
    def _think_and_select(self, context: Dict[str, Any], candidates: List[tuple]) -> tuple:
        best_item = None
        best_score = -1
        user_profile = context.get("user_profile", {})
        
        for item, retrieval_score in candidates:
            score = retrieval_score
            # Color match boost
            color_prefs = user_profile.get("color_preferences", [])
            if item.get("color_primary", "").lower() in [c.lower() for c in color_prefs]:
                score += 0.25
            
            if score > best_score:
                best_score = score
                best_item = item
        return best_item, min(best_score, 1.0)
    
    def _generate_reasoning(self, context: Dict[str, Any], selected_item: Dict[str, Any]) -> str:
        user_profile = context.get("user_profile", {})
        item_color = selected_item.get("color_primary", "")
        item_style = selected_item.get("style_aesthetic", "")
        
        reasons = []
        if item_color: reasons.append(f"色調'{item_color}'符合您的偏好")
        if item_style: reasons.append(f"風格'{item_style}'展現獨特氣質")
        
        return "，".join(reasons) + "。" if reasons else "這件衣服非常適合您的當前場合。"
    
    def _generate_vton_prompt(self, context: Dict[str, Any], selected_item: Dict[str, Any]) -> str:
        color = selected_item.get("color_primary", "neutral")
        category = selected_item.get("category", "outfit")
        desc = selected_item.get("complete_description", "")
        return f"A photorealistic image of a model wearing a {color} {category}, {desc}, cinematic lighting, 8k resolution."

    def _generate_vton_prompt_for_pair(self, context: Dict[str, Any], top: Dict[str, Any], bottom: Dict[str, Any]) -> str:
        top_color = top.get("color_primary", "neutral")
        bottom_color = bottom.get("color_primary", "neutral")
        top_cat = top.get("category", "top")
        bottom_cat = bottom.get("category", "bottom")
        
        return (f"A photorealistic image of a model wearing a {top_color} {top_cat} paired with matching {bottom_color} {bottom_cat}. "
                f"Tone-on-tone outfit style. Cinematic lighting, professional photography, 8k resolution, highly detailed.")

    def _extract_filename(self, item: Dict[str, Any]) -> str:
        for key in ["filename", "image_url", "image_path", "id"]:
            if key in item: return item[key]
        return "unknown.jpg"

    def _create_empty_output(self, context: Dict[str, Any]) -> RecommendationOutput:
        return RecommendationOutput(
            task_id="error", selected_outfit={}, reasoning_log="No matches found", vton_generation_prompt=""
        )

if __name__ == "__main__":
    # Test block
    print("Running Recommendation Logic Test...")
    try:
        recommender = OutfitRecommenderV2()
        output = recommender.recommend(scenario="casual_daily")
        print(f"Result JSON:\n{output.to_json()}")
    except Exception as e:
        print(f"Error: {e}")
