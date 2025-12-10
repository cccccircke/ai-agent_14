"""
Outfit Planner Agent
Recommends outfits based on context, embeddings, and descriptions.
Uses CLIP embeddings for compatibility matching and descriptions for filtering.
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class OutfitPlanner:
    """
    Agent responsible for planning and recommending outfits.
    """
    
    def __init__(
        self,
        descriptions_path: str = "outfit_descriptions.json",
        embeddings_path: str = "outfit_embeddings.npy",
        catalog_index_path: str = "catalog_index.json"
    ):
        """
        Initialize the Outfit Planner.
        
        Args:
            descriptions_path: Path to outfit descriptions JSON
            embeddings_path: Path to outfit embeddings numpy file
            catalog_index_path: Path to catalog index JSON
        """
        self.descriptions_path = descriptions_path
        self.embeddings_path = embeddings_path
        self.catalog_index_path = catalog_index_path
        
        # Load data
        self.descriptions = self._load_descriptions()
        self.embeddings = self._load_embeddings()
        self.catalog_index = self._load_catalog_index()
        
        # Validate data
        self._validate_data()
    
    def _load_descriptions(self) -> Dict:
        """Load outfit descriptions from JSON file."""
        if not os.path.exists(self.descriptions_path):
            raise FileNotFoundError(f"Descriptions file not found: {self.descriptions_path}")
        
        with open(self.descriptions_path, 'r', encoding='utf-8') as f:
            descriptions = json.load(f)
        
        print(f"✓ Loaded {len(descriptions)} outfit descriptions")
        return descriptions
    
    def _load_embeddings(self) -> np.ndarray:
        """Load outfit embeddings from numpy file."""
        if not os.path.exists(self.embeddings_path):
            raise FileNotFoundError(f"Embeddings file not found: {self.embeddings_path}")
        
        embeddings = np.load(self.embeddings_path)
        print(f"✓ Loaded embeddings with shape: {embeddings.shape}")
        return embeddings
    
    def _load_catalog_index(self) -> Dict:
        """Load catalog index from JSON file."""
        if not os.path.exists(self.catalog_index_path):
            raise FileNotFoundError(f"Catalog index not found: {self.catalog_index_path}")
        
        with open(self.catalog_index_path, 'r', encoding='utf-8') as f:
            catalog_index = json.load(f)
        
        print(f"✓ Loaded catalog index with {len(catalog_index)} items")
        return catalog_index
    
    def _validate_data(self):
        """Validate that all data sources are consistent."""
        descriptions_count = len(self.descriptions)
        embeddings_count = self.embeddings.shape[0]
        catalog_count = len(self.catalog_index)
        
        if not (descriptions_count == embeddings_count == catalog_count):
            print(f"⚠️  Warning: Data count mismatch!")
            print(f"   Descriptions: {descriptions_count}")
            print(f"   Embeddings: {embeddings_count}")
            print(f"   Catalog: {catalog_count}")
        else:
            print(f"✓ Data validation passed: {descriptions_count} items consistent")
    
    def filter_by_temperature(self, temperature: float, comfort_analysis: Dict) -> List[str]:
        """
        Filter outfits based on temperature and comfort requirements.
        
        Args:
            temperature: Current temperature in Celsius
            comfort_analysis: Dictionary with comfort level and recommendations
            
        Returns:
            List of suitable outfit filenames
        """
        comfort_level = comfort_analysis.get('comfort_level', 'comfortable')
        layers_needed = comfort_analysis.get('layers_needed', 'light')
        
        suitable_outfits = []
        
        for filename, desc in self.descriptions.items():
            material = desc.get('material', '').lower()
            fit = desc.get('fit_silhouette', '').lower()
            length = desc.get('length', '').lower()
            sleeve = desc.get('sleeve_length', '').lower()
            
            # Cold weather: prefer heavy materials, layers, long sleeves
            if comfort_level == 'cold':
                if layers_needed == 'heavy':
                    if 'wool' in material or 'cotton' in material or 'jacket' in fit.lower():
                        suitable_outfits.append(filename)
                elif layers_needed == 'medium':
                    if 'cotton' in material or 'wool' in material:
                        suitable_outfits.append(filename)
            
            # Comfortable weather: flexible options
            elif comfort_level == 'comfortable':
                suitable_outfits.append(filename)
            
            # Warm/Hot weather: prefer light materials, short sleeves
            elif comfort_level in ['warm', 'hot']:
                if 'linen' in material or 'cotton' in material or 'silk' in material:
                    if 'short' in sleeve or 'sleeveless' in sleeve:
                        suitable_outfits.append(filename)
                else:
                    # Still include if not heavy
                    if 'wool' not in material and 'down' not in material:
                        suitable_outfits.append(filename)
        
        return suitable_outfits if suitable_outfits else list(self.descriptions.keys())
    
    def filter_by_occasion_formality(self, formality: str, occasion: str) -> List[str]:
        """
        Filter outfits based on occasion and formality level.
        
        Args:
            formality: Formality level (formal, business_formal, business_casual, casual, sporty)
            occasion: Type of occasion (上班, 派對, etc.)
            
        Returns:
            List of suitable outfit filenames
        """
        suitable_outfits = []
        
        for filename, desc in self.descriptions.items():
            style = (desc.get('style_aesthetic', '') or '').lower()
            category = (desc.get('category', '') or '').lower()
            subcategory = (desc.get('subcategory', '') or '').lower()
            
            # Formal events: prefer classic, formal styles
            if formality == 'formal':
                if 'classic' in style or 'formal' in style or 'dress' in category:
                    suitable_outfits.append(filename)
            
            # Business formal: prefer business-appropriate styles
            elif formality == 'business_formal':
                if ('business' in style or 'classic' in style or 'formal' in style or
                    'jacket' in subcategory or 'dress' in category):
                    suitable_outfits.append(filename)
            
            # Business casual: moderate formality
            elif formality == 'business_casual':
                if not ('sporty' in style or 'athletic' in style):
                    suitable_outfits.append(filename)
            
            # Casual: most styles acceptable
            elif formality == 'casual':
                suitable_outfits.append(filename)
            
            # Sporty: prefer athletic/sporty styles
            elif formality == 'sporty':
                if 'sporty' in style or 'athletic' in subcategory:
                    suitable_outfits.append(filename)
        
        return suitable_outfits if suitable_outfits else list(self.descriptions.keys())
    
    def filter_by_colors(
        self,
        preferred_colors: Optional[List[str]] = None,
        avoid_colors: Optional[List[str]] = None,
        season_type: Optional[str] = None
    ) -> List[str]:
        """
        Filter outfits based on color preferences and seasonal color analysis.
        
        Args:
            preferred_colors: List of preferred colors
            avoid_colors: List of colors to avoid
            season_type: Seasonal color type (spring, summer, autumn, winter)
            
        Returns:
            List of suitable outfit filenames
        """
        suitable_outfits = []
        
        # Default recommendations for seasonal colors
        seasonal_colors = {
            'spring': ['pastel pink', 'soft green', 'light blue', 'cream'],
            'summer': ['white', 'light blue', 'bright colors', 'pastels'],
            'autumn': ['brown', 'orange', 'rust', 'gold'],
            'winter': ['black', 'white', 'navy', 'burgundy', 'gray'],
            'cool': ['cool gray', 'navy', 'white', 'soft pink', 'powder blue'],
            'warm': ['warm beige', 'orange', 'gold', 'warm brown']
        }
        
        preferred = set([c.lower() for c in (preferred_colors or [])])
        avoid = set([c.lower() for c in (avoid_colors or [])])
        seasonal = set([c.lower() for c in seasonal_colors.get(season_type or '', [])])
        
        for filename, desc in self.descriptions.items():
            primary = (desc.get('color_primary', '') or '').lower()
            secondary = (desc.get('color_secondary', '') or '').lower()
            
            # Check if colors match preferences or seasonal palette
            colors_match = False
            
            # If no preferences specified, use seasonal colors or accept all
            if not preferred and not avoid:
                if season_type and season_type in seasonal_colors:
                    # Check against seasonal palette
                    for seasonal_color in seasonal_colors[season_type]:
                        if seasonal_color in primary or seasonal_color in secondary:
                            colors_match = True
                            break
                else:
                    # No season info, accept all
                    colors_match = True
            else:
                # Check preferred colors
                if preferred:
                    for pref in preferred:
                        if pref in primary or pref in secondary:
                            colors_match = True
                            break
                else:
                    colors_match = True
            
            # Check avoid colors
            avoid_match = False
            if avoid:
                for avoid_color in avoid:
                    if avoid_color in primary or avoid_color in secondary:
                        avoid_match = True
                        break
            
            if colors_match and not avoid_match:
                suitable_outfits.append(filename)
        
        return suitable_outfits if suitable_outfits else list(self.descriptions.keys())
    
    def calculate_embedding_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1 (higher is more similar)
        """
        # Normalize embeddings
        emb1_norm = embedding1 / (np.linalg.norm(embedding1) + 1e-8)
        emb2_norm = embedding2 / (np.linalg.norm(embedding2) + 1e-8)
        
        # Cosine similarity
        similarity = np.dot(emb1_norm, emb2_norm)
        return float(similarity)
    
    def find_complementary_outfits(
        self,
        base_outfit_filename: str,
        candidate_filenames: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find outfits that complement a base outfit using embedding similarity.
        
        Args:
            base_outfit_filename: Filename of the base outfit
            candidate_filenames: List of candidate outfit filenames to compare
            top_k: Number of top matches to return
            
        Returns:
            List of (filename, similarity_score) tuples, sorted by similarity
        """
        if base_outfit_filename not in self.catalog_index:
            raise ValueError(f"Outfit '{base_outfit_filename}' not in catalog")
        
        base_idx = self.catalog_index[base_outfit_filename]['embedding_index']
        base_embedding = self.embeddings[base_idx]
        
        similarities = []
        
        for candidate in candidate_filenames:
            if candidate == base_outfit_filename:
                continue
            
            if candidate not in self.catalog_index:
                continue
            
            candidate_idx = self.catalog_index[candidate]['embedding_index']
            candidate_embedding = self.embeddings[candidate_idx]
            
            similarity = self.calculate_embedding_similarity(base_embedding, candidate_embedding)
            similarities.append((candidate, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def recommend_complete_outfit(self, context: Dict) -> Dict:
        """
        Generate a complete outfit recommendation based on daily context.
        
        Args:
            context: Daily context dictionary from ContextCollectorAgent
                     Should contain:
                     - weather: temperature, humidity, condition
                     - daily_context: occasion, formality, color_preference, avoid_colors
                     - comfort_analysis: comfort_level, recommendations
                     - user_profile_summary: color_season, style_preferences
            
        Returns:
            Dictionary with outfit recommendations
        """
        print("\n" + "="*60)
        print("👕 穿搭推薦系統")
        print("="*60)
        
        # Extract context information
        weather = context.get('weather', {})
        daily_context = context.get('daily_context', {})
        comfort_analysis = context.get('comfort_analysis', {})
        user_profile = context.get('user_profile_summary', {})
        
        temperature = weather.get('temperature', 20)
        occasion = daily_context.get('occasion', '休閒外出')
        formality = daily_context.get('formality', 'casual')
        color_pref = daily_context.get('color_preference')
        avoid_colors = daily_context.get('avoid_colors')
        season_type = user_profile.get('color_season', 'summer')
        
        print(f"\n📊 情境分析:")
        print(f"  溫度: {temperature}°C")
        print(f"  場合: {occasion}")
        print(f"  正式程度: {formality}")
        print(f"  天氣: {weather.get('weather_condition', '未知')}")
        
        # Apply filters in sequence
        print(f"\n🔍 正在進行穿搭篩選...")
        
        # Filter 1: Temperature
        temp_suitable = self.filter_by_temperature(temperature, comfort_analysis)
        print(f"  ✓ 溫度過濾: {len(temp_suitable)} 件衣服")
        
        # Filter 2: Occasion and Formality
        occasion_suitable = self.filter_by_occasion_formality(formality, occasion)
        print(f"  ✓ 場合過濾: {len(occasion_suitable)} 件衣服")
        
        # Intersect first two filters
        candidates = list(set(temp_suitable) & set(occasion_suitable))
        print(f"  ✓ 綜合過濾: {len(candidates)} 件衣服")
        
        # Filter 3: Colors
        color_suitable = self.filter_by_colors(color_pref, avoid_colors, season_type)
        candidates = list(set(candidates) & set(color_suitable))
        print(f"  ✓ 色彩過濾: {len(candidates)} 件衣服")
        
        # Categorize recommendations
        recommendations = self._categorize_outfits(candidates)
        
        # Generate recommendation report
        result = {
            'timestamp': datetime.now().isoformat(),
            'context_summary': {
                'temperature': temperature,
                'weather': weather.get('weather_condition'),
                'occasion': occasion,
                'formality': formality,
                'color_preference': color_pref,
                'avoid_colors': avoid_colors
            },
            'recommendations': recommendations,
            'total_suitable': len(candidates),
            'comfort_tips': comfort_analysis.get('recommendations', [])
        }
        
        # Print recommendations
        self._print_recommendations(result)
        
        return result
    
    def _categorize_outfits(self, outfit_filenames: List[str]) -> Dict:
        """
        Categorize outfits by type (Upper, Lower, Dress, Set).
        
        Args:
            outfit_filenames: List of outfit filenames to categorize
            
        Returns:
            Dictionary with categories as keys and outfit lists as values
        """
        categorized = {
            'Upper': [],
            'Lower': [],
            'Dress': [],
            'Set': [],
            'Other': []
        }
        
        for filename in outfit_filenames:
            if filename in self.descriptions:
                desc = self.descriptions[filename]
                category = desc.get('category', 'Other')
                
                outfit_info = {
                    'filename': filename,
                    'subcategory': desc.get('subcategory', ''),
                    'color': desc.get('color_primary', ''),
                    'style': desc.get('style_aesthetic', ''),
                    'description': desc.get('complete_description', '')
                }
                
                if category in categorized:
                    categorized[category].append(outfit_info)
                else:
                    categorized['Other'].append(outfit_info)
        
        # Remove empty categories
        return {k: v for k, v in categorized.items() if v}
    
    def _print_recommendations(self, result: Dict):
        """
        Print outfit recommendations in a human-readable format.
        
        Args:
            result: Recommendation result dictionary
        """
        print("\n" + "="*60)
        print("📋 推薦結果")
        print("="*60)
        
        context_summary = result['context_summary']
        print(f"\n天氣狀況: {context_summary['temperature']}°C, {context_summary['weather']}")
        print(f"場合: {context_summary['occasion']}")
        print(f"正式程度: {context_summary['formality']}")
        
        if context_summary['color_preference']:
            print(f"色彩偏好: {', '.join(context_summary['color_preference'])}")
        
        print(f"\n💡 舒適建議:")
        for tip in result['comfort_tips']:
            print(f"  • {tip}")
        
        print(f"\n👚 衣服推薦 (共 {result['total_suitable']} 件):")
        
        for category, outfits in result['recommendations'].items():
            print(f"\n【{category}】")
            for outfit in outfits[:3]:  # Show top 3 per category
                print(f"  • {outfit['filename']}: {outfit['subcategory']}")
                print(f"    顏色: {outfit['color']}")
                if outfit['description']:
                    print(f"    描述: {outfit['description'][:80]}...")
    
    def save_recommendation(self, result: Dict, output_path: str = "outfit_recommendation.json"):
        """
        Save recommendation result to JSON file.
        
        Args:
            result: Recommendation result dictionary
            output_path: Path to save the JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✓ 推薦結果已儲存至: {output_path}")


def main():
    """
    Example usage of Outfit Planner.
    """
    # Initialize planner
    print("初始化穿搭推薦系統...")
    planner = OutfitPlanner()
    
    # Example context (would normally come from ContextCollectorAgent)
    example_context = {
        'weather': {
            'temperature': 22.0,
            'humidity': 65,
            'weather_condition': '晴朗',
            'wind_speed': 3.5
        },
        'daily_context': {
            'occasion': '上班',
            'formality': 'business_casual',
            'formality_name': '商務休閒',
            'has_dress_code': False,
            'activities': ['上班'],
            'duration_hours': 8.0,
            'color_preference': ['blue', 'white'],
            'avoid_colors': ['red'],
            'special_requirements': None
        },
        'comfort_analysis': {
            'comfort_level': 'comfortable',
            'layers_needed': 'light',
            'recommendations': ['輕薄外套即可', '可穿長袖或短袖'],
            'temperature': 22.0
        },
        'user_profile_summary': {
            'name': '測試使用者',
            'color_season': 'cool',
            'style_preferences': ['現代風', '簡約風']
        }
    }
    
    # Generate recommendations
    recommendations = planner.recommend_complete_outfit(example_context)
    
    # Save recommendations
    planner.save_recommendation(recommendations)


if __name__ == "__main__":
    main()
