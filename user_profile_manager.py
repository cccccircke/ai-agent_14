"""
User Profile Manager
Handles user profile creation, storage, and management.
Includes first-time setup wizard for collecting user information.
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional


class UserProfileManager:
    """
    Manages user profile including location, style preferences, color analysis, and settings.
    """
    
    def __init__(self, profile_path: str = "user_profile.json"):
        """
        Initialize the User Profile Manager.
        
        Args:
            profile_path: Path to the user profile JSON file
        """
        self.profile_path = profile_path
        self.profile = None
    
    def profile_exists(self) -> bool:
        """
        Check if a user profile already exists.
        
        Returns:
            True if profile exists, False otherwise
        """
        return os.path.exists(self.profile_path)
    
    def load_profile(self) -> Optional[Dict]:
        """
        Load existing user profile from file.
        
        Returns:
            User profile dictionary or None if not found
        """
        if not self.profile_exists():
            return None
        
        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                self.profile = json.load(f)
            print(f"✓ 已載入使用者資料: {self.profile.get('name', 'User')}")
            return self.profile
        except Exception as e:
            print(f"Error loading profile: {e}")
            return None
    
    def save_profile(self, profile: Dict):
        """
        Save user profile to file.
        
        Args:
            profile: User profile dictionary to save
        """
        profile['last_updated'] = datetime.now().isoformat()
        
        with open(self.profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        self.profile = profile
        print(f"✓ 使用者資料已儲存")
    
    def run_first_time_setup(self) -> Dict:
        """
        Run interactive first-time setup wizard to collect user information.
        
        Returns:
            Complete user profile dictionary
        """
        print("\n" + "="*60)
        print("👋 歡迎使用智能衣櫥推薦系統！")
        print("="*60)
        print("\n讓我們先設定您的個人資料，以便提供更精準的穿搭建議。\n")
        
        profile = {}
        
        # Basic Information
        print("📋 基本資訊")
        print("-" * 40)
        profile['name'] = input("請輸入您的名字 (或暱稱): ").strip() or "User"
        
        # Location
        print("\n📍 位置資訊")
        print("-" * 40)
        profile['location'] = {
            'city': input("您居住的城市 (例如: Taipei): ").strip() or "Taipei",
            'country_code': input("國家代碼 (例如: TW): ").strip() or "TW"
        }
        
        # Style Preferences
        print("\n✨ 風格偏好")
        print("-" * 40)
        print("常見風格: 休閒風、正式商務、街頭風、韓系、日系、極簡風、復古風")
        preferred_styles = input("您喜歡的風格 (可多選，用逗號分隔): ").strip()
        profile['style_preferences'] = [s.strip() for s in preferred_styles.split(',')] if preferred_styles else ["休閒風"]
        
        # Color Analysis (季節色彩分析)
        print("\n🎨 色彩分析")
        print("-" * 40)
        print("季節色彩類型:")
        print("  1. 春季型 (Spring) - 溫暖明亮的色彩")
        print("  2. 夏季型 (Summer) - 冷色調柔和色彩")
        print("  3. 秋季型 (Autumn) - 溫暖深沉的色彩")
        print("  4. 冬季型 (Winter) - 冷色調鮮明色彩")
        print("  5. 不確定")
        
        season_choice = input("選擇您的季節色彩類型 (1-5): ").strip()
        season_map = {
            '1': 'spring',
            '2': 'summer',
            '3': 'autumn',
            '4': 'winter',
            '5': 'unknown'
        }
        
        color_season = season_map.get(season_choice, 'unknown')
        
        # Define color palettes for each season
        color_palettes = {
            'spring': {
                'best_colors': ['coral', 'peach', 'warm yellow', 'light orange', 'turquoise', 'warm green'],
                'avoid_colors': ['black', 'pure white', 'cool gray', 'navy'],
                'neutrals': ['ivory', 'camel', 'warm beige', 'light brown']
            },
            'summer': {
                'best_colors': ['soft pink', 'lavender', 'powder blue', 'cool gray', 'mauve', 'soft white'],
                'avoid_colors': ['orange', 'warm yellow', 'bright warm colors'],
                'neutrals': ['soft white', 'cool gray', 'navy', 'cool brown']
            },
            'autumn': {
                'best_colors': ['rust', 'olive', 'burnt orange', 'warm brown', 'mustard', 'deep teal'],
                'avoid_colors': ['bright pink', 'icy colors', 'cool blue'],
                'neutrals': ['camel', 'warm brown', 'olive', 'cream']
            },
            'winter': {
                'best_colors': ['true red', 'royal blue', 'emerald', 'pure white', 'black', 'hot pink'],
                'avoid_colors': ['orange', 'warm yellow', 'warm browns'],
                'neutrals': ['black', 'pure white', 'navy', 'cool gray']
            },
            'unknown': {
                'best_colors': [],
                'avoid_colors': [],
                'neutrals': []
            }
        }
        
        profile['color_analysis'] = {
            'season_type': color_season,
            'palette': color_palettes.get(color_season, color_palettes['unknown'])
        }
        
        # Additional color preferences
        favorite_colors = input("\n您最喜歡的顏色 (可多選，用逗號分隔): ").strip()
        profile['color_analysis']['favorite_colors'] = [c.strip() for c in favorite_colors.split(',')] if favorite_colors else []
        
        dislike_colors = input("您不喜歡或想避免的顏色 (可多選，用逗號分隔): ").strip()
        profile['color_analysis']['dislike_colors'] = [c.strip() for c in dislike_colors.split(',')] if dislike_colors else []
        
        # Body Type & Fit Preferences
        print("\n👗 體型與版型偏好")
        print("-" * 40)
        print("常見版型: 合身、寬鬆、oversized、修身")
        fit_preferences = input("您偏好的版型 (可多選，用逗號分隔): ").strip()
        profile['fit_preferences'] = [f.strip() for f in fit_preferences.split(',')] if fit_preferences else ["合身"]
        
        # Lifestyle & Occasions
        print("\n📅 生活型態")
        print("-" * 40)
        print("常見場合: 上班、休閒、運動、約會、正式場合")
        common_occasions = input("您常出現的場合 (可多選，用逗號分隔): ").strip()
        profile['common_occasions'] = [o.strip() for o in common_occasions.split(',')] if common_occasions else ["休閒"]
        
        # Comfort Preferences
        print("\n🌡️ 溫度偏好")
        print("-" * 40)
        temp_pref = input("您對溫度的敏感度 (怕冷/正常/怕熱): ").strip() or "正常"
        profile['temperature_sensitivity'] = temp_pref
        
        # Metadata
        profile['created_at'] = datetime.now().isoformat()
        profile['last_updated'] = datetime.now().isoformat()
        profile['version'] = "1.0"
        
        print("\n" + "="*60)
        print("✓ 個人資料設定完成！")
        print("="*60)
        
        return profile
    
    def update_profile(self, updates: Dict):
        """
        Update specific fields in the user profile.
        
        Args:
            updates: Dictionary with fields to update
        """
        if not self.profile:
            self.load_profile()
        
        if not self.profile:
            print("No profile found. Please run setup first.")
            return
        
        self.profile.update(updates)
        self.save_profile(self.profile)
    
    def display_profile(self, profile: Optional[Dict] = None):
        """
        Display user profile in a readable format.
        
        Args:
            profile: Profile to display (uses loaded profile if None)
        """
        if profile is None:
            profile = self.profile
        
        if not profile:
            print("No profile to display.")
            return
        
        print("\n" + "="*60)
        print("👤 使用者資料")
        print("="*60)
        
        print(f"\n📋 名字: {profile.get('name', 'N/A')}")
        
        # Location
        location = profile.get('location', {})
        print(f"📍 位置: {location.get('city', 'N/A')}, {location.get('country_code', 'N/A')}")
        
        # Style Preferences
        styles = profile.get('style_preferences', [])
        print(f"✨ 風格偏好: {', '.join(styles) if styles else 'N/A'}")
        
        # Color Analysis
        color_analysis = profile.get('color_analysis', {})
        season_names = {
            'spring': '春季型',
            'summer': '夏季型',
            'autumn': '秋季型',
            'winter': '冬季型',
            'unknown': '未設定'
        }
        season = season_names.get(color_analysis.get('season_type', 'unknown'), '未設定')
        print(f"🎨 色彩季節: {season}")
        
        if color_analysis.get('favorite_colors'):
            print(f"   喜愛顏色: {', '.join(color_analysis['favorite_colors'])}")
        
        # Fit Preferences
        fits = profile.get('fit_preferences', [])
        print(f"👗 版型偏好: {', '.join(fits) if fits else 'N/A'}")
        
        # Common Occasions
        occasions = profile.get('common_occasions', [])
        print(f"📅 常見場合: {', '.join(occasions) if occasions else 'N/A'}")
        
        # Temperature Sensitivity
        print(f"🌡️  溫度敏感: {profile.get('temperature_sensitivity', 'N/A')}")
        
        print(f"\n⏰ 建立時間: {profile.get('created_at', 'N/A')}")
        print(f"🔄 更新時間: {profile.get('last_updated', 'N/A')}")
        
        print("\n" + "="*60 + "\n")
    
    def get_or_create_profile(self) -> Dict:
        """
        Get existing profile or run setup if it doesn't exist.
        
        Returns:
            User profile dictionary
        """
        if self.profile_exists():
            profile = self.load_profile()
            return profile
        else:
            print("\n未找到使用者資料。")
            profile = self.run_first_time_setup()
            self.save_profile(profile)
            return profile


def main():
    """
    Example usage of User Profile Manager.
    """
    manager = UserProfileManager()
    
    # Get or create profile
    profile = manager.get_or_create_profile()
    
    # Display profile
    manager.display_profile(profile)
    
    # Example: Update profile
    # manager.update_profile({
    #     'style_preferences': ['極簡風', '韓系']
    # })


if __name__ == "__main__":
    main()
