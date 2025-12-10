"""
Context Collector Agent
Collects external information (weather) and daily context through interactive questions.
Asks user about occasion, formality, dress code, and preferences for each outfit session.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional, List


class ContextCollectorAgent:
    """
    Agent responsible for collecting contextual information through interactive prompts.
    """
    
    def __init__(self, user_profile: Optional[Dict] = None, api_key: Optional[str] = None):
        """
        Initialize the Context Collector Agent.
        
        Args:
            user_profile: User profile dictionary
            api_key: WeatherAPI key for weather data
        """
        self.user_profile = user_profile or {}
        self.api_key = api_key or "API_KEY_HERE"  # API key (free trial smpe 24 dec)
        self.weather_base_url = "https://api.weatherapi.com/v1/current.json" 

    def get_weather_data(self, city: Optional[str] = None, country_code: Optional[str] = None) -> Dict:
        """
        Fetch current weather data including temperature and humidity.
        Uses user profile location if not specified.
        
        Args:
            city: City name (uses profile if None)
            country_code: Country code (uses profile if None)
            
        Returns:
            Dictionary containing weather information
        """
        # Use profile location if not specified
        if city is None:
            location = self.user_profile.get('location', {})
            city = city or location.get('city', 'Taipei')
        
        if not self.api_key:
            print("⚠️  未提供天氣 API 密鑰，使用模擬資料")
            return self._get_mock_weather_data(city)
        
        try:
            params = {
                'key': self.api_key,  # WeatherAPI requires 'key' for the API key
                'q': city,           # Query parameter for city
                'aqi': 'no'          # Disable air quality data for simplicity
            }
            
            response = requests.get(self.weather_base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            weather_info = {
                'temperature': data['current']['temp_c'],  # Temperature in Celsius
                'feels_like': data['current']['feelslike_c'],  # Feels-like temperature
                'humidity': data['current']['humidity'],  # Humidity percentage
                'weather_condition': data['current']['condition']['text'],  # Weather condition text
                'wind_speed': data['current']['wind_kph'],  # Wind speed in kph
                'city': city,
                'timestamp': datetime.now().isoformat()
            }
            
            return weather_info
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️  獲取天氣資料時發生錯誤: {e}")
            print("使用模擬天氣資料")
            return self._get_mock_weather_data(city)
    
    def _get_mock_weather_data(self, city: str = "Taipei") -> Dict: # mock data if the API key is not avail
        """
        Generate mock weather data for testing without API key.
        
        Args:
            city: City name
            
        Returns:
            Mock weather dictionary
        """
        return {
            'temperature': 22.0,
            'feels_like': 21.5,
            'humidity': 65,
            'weather_condition': 'Partly cloudy',
            'wind_speed': 3.5,
            'city': city,
            'timestamp': datetime.now().isoformat(),
            'mock_data': True
        }
    
    def ask_daily_context(self) -> Dict:
        """
        Ask user interactive questions about today's context.
        
        Returns:
            Dictionary containing daily context information
        """
        print("\n" + "="*60)
        print("📋 今日穿搭情境")
        print("="*60)
        print("\n請回答以下問題，幫助我們為您推薦最適合的穿搭。\n")
        
        context = {}
        
        # Occasion
        print("🎯 場合與活動")
        print("-" * 40)
        print("常見場合: 上班、休閒外出、約會、正式會議、派對、運動、居家")
        
        # Show user's common occasions if available
        common_occasions = self.user_profile.get('common_occasions', [])
        if common_occasions:
            print(f"您常見的場合: {', '.join(common_occasions)}")
        
        occasion = input("\n今天主要的場合或活動是什麼？ ").strip()
        context['occasion'] = occasion or "休閒外出"
        
        # Formality Level
        print("\n👔 正式程度")
        print("-" * 40)
        print("  1. 非常正式 (Formal) - 西裝、晚禮服")
        print("  2. 商務正式 (Business Formal) - 正式套裝")
        print("  3. 商務休閒 (Business Casual) - 襯衫配休閒褲")
        print("  4. 休閒 (Casual) - 日常休閒服")
        print("  5. 運動休閒 (Sporty/Athleisure) - 運動風格")
        
        formality_choice = input("\n選擇正式程度 (1-5): ").strip()
        formality_map = {
            '1': {'level': 'formal', 'name': '非常正式'},
            '2': {'level': 'business_formal', 'name': '商務正式'},
            '3': {'level': 'business_casual', 'name': '商務休閒'},
            '4': {'level': 'casual', 'name': '休閒'},
            '5': {'level': 'sporty', 'name': '運動休閒'}
        }
        
        formality_info = formality_map.get(formality_choice, formality_map['4'])
        context['formality'] = formality_info['level']
        context['formality_name'] = formality_info['name']
        
        # Dress Code
        print("\n📜 著裝要求")
        print("-" * 40)
        has_dress_code = input("是否有特定的著裝要求或規定？(有/無): ").strip().lower()
        
        if has_dress_code in ['有', 'y', 'yes', '是']:
            dress_code = input("請描述著裝要求: ").strip()
            context['dress_code'] = dress_code
            context['has_dress_code'] = True
        else:
            context['dress_code'] = None
            context['has_dress_code'] = False
        
        # Activities and Duration
        print("\n📅 活動詳情")
        print("-" * 40)
        activities = input("今天的主要活動 (用逗號分隔，例如: 會議,午餐,簡報): ").strip()
        context['activities'] = [a.strip() for a in activities.split(',')] if activities else ["一般活動"]
        
        duration = input("預計穿著時間 (小時): ").strip()
        try:
            context['duration_hours'] = float(duration)
        except ValueError:
            context['duration_hours'] = 8.0
        
        outdoor_time = input("預計戶外時間 (小時): ").strip()
        try:
            context['outdoor_time'] = float(outdoor_time)
        except ValueError:
            context['outdoor_time'] = 2.0
        
        # Style Preference for Today
        print("\n✨ 今日風格偏好")
        print("-" * 40)
        
        # Show user's preferred styles if available
        user_styles = self.user_profile.get('style_preferences', [])
        if user_styles:
            print(f"您偏好的風格: {', '.join(user_styles)}")
        
        print("常見風格: 休閒風、正式商務、街頭風、韓系、日系、極簡風、復古風")
        style_today = input("\n今天想要呈現什麼風格？ ").strip()
        context['style_preference'] = style_today or (user_styles[0] if user_styles else "休閒風")
        
        # Color Preference for Today
        print("\n🎨 今日色彩偏好")
        print("-" * 40)
        
        # Show color season recommendations if available
        color_analysis = self.user_profile.get('color_analysis', {})
        season_type = color_analysis.get('season_type')
        
        if season_type and season_type != 'unknown':
            palette = color_analysis.get('palette', {})
            best_colors = palette.get('best_colors', [])
            if best_colors:
                print(f"根據您的色彩季節，建議顏色: {', '.join(best_colors[:5])}")
        
        color_pref = input("\n今天想穿什麼顏色？(可多選，用逗號分隔): ").strip()
        context['color_preference'] = [c.strip() for c in color_pref.split(',')] if color_pref else None
        
        avoid_colors = input("今天想避免的顏色？(可多選，用逗號分隔): ").strip()
        context['avoid_colors'] = [c.strip() for c in avoid_colors.split(',')] if avoid_colors else []
        
        # Special Requirements
        print("\n💡 特殊需求")
        print("-" * 40)
        special_req = input("其他特殊需求或注意事項？(例如: 需要方便活動、需要口袋): ").strip()
        context['special_requirements'] = special_req if special_req else None
        
        # Add timestamp
        context['timestamp'] = datetime.now().isoformat()
        
        print("\n✓ 情境資訊收集完成！")
        
        return context
    
    def analyze_temperature_comfort(self, temperature: float) -> Dict:
        """
        Analyze temperature and provide clothing recommendations.
        Considers user's temperature sensitivity.
        
        Args:
            temperature: Temperature in Celsius
            
        Returns:
            Dictionary with comfort analysis and recommendations
        """
        # Adjust for user's temperature sensitivity
        temp_sensitivity = self.user_profile.get('temperature_sensitivity', '正常')
        
        adjusted_temp = temperature
        if temp_sensitivity in ['怕冷', 'cold-sensitive']:
            adjusted_temp -= 3  # Treat as 3 degrees colder
        elif temp_sensitivity in ['怕熱', 'heat-sensitive']:
            adjusted_temp += 3  # Treat as 3 degrees warmer
        
        if adjusted_temp < 10:
            comfort_level = "cold"
            layers_needed = "heavy"
            recommendations = ["需要厚外套或大衣", "建議多層穿搭", "可考慮圍巾、手套等配件", "選擇保暖材質如羊毛、羽絨"]
        elif adjusted_temp < 18:
            comfort_level = "cool"
            layers_needed = "medium"
            recommendations = ["需要外套", "建議薄毛衣或長袖襯衫", "可穿長褲", "洋蔥式穿搭方便調節"]
        elif adjusted_temp < 25:
            comfort_level = "comfortable"
            layers_needed = "light"
            recommendations = ["輕薄外套即可", "可穿長袖或短袖", "舒適溫度範圍", "注意室內外溫差"]
        elif adjusted_temp < 30:
            comfort_level = "warm"
            layers_needed = "minimal"
            recommendations = ["穿短袖或無袖", "選擇透氣材質如棉、麻", "避免厚重衣物", "淺色衣物較不吸熱"]
        else:
            comfort_level = "hot"
            layers_needed = "minimal"
            recommendations = ["穿著清涼衣物", "選擇吸汗透氣材質", "避免深色和厚重衣物", "注意防曬"]
        
        return {
            'comfort_level': comfort_level,
            'layers_needed': layers_needed,
            'recommendations': recommendations,
            'temperature': temperature,
            'adjusted_temperature': adjusted_temp,
            'user_sensitivity': temp_sensitivity
        }
    
    def collect_complete_context(self, ask_questions: bool = True) -> Dict:
        """
        Collect all contextual information.
        
        Args:
            ask_questions: Whether to ask interactive questions (False for automated mode)
            
        Returns:
            Complete context dictionary
        """
        # Get weather data
        print("\n🌤️  正在獲取天氣資料...")
        weather = self.get_weather_data()
        
        # Ask daily context questions
        if ask_questions:
            daily_context = self.ask_daily_context()
        else:
            # Use default values for automated mode
            daily_context = {
                'occasion': '休閒外出',
                'formality': 'casual',
                'formality_name': '休閒',
                'has_dress_code': False,
                'dress_code': None,
                'activities': ['一般活動'],
                'duration_hours': 8.0,
                'outdoor_time': 2.0,
                'style_preference': self.user_profile.get('style_preferences', ['休閒風'])[0],
                'color_preference': None,
                'avoid_colors': [],
                'special_requirements': None,
                'timestamp': datetime.now().isoformat()
            }
        
        # Analyze temperature comfort
        comfort_analysis = self.analyze_temperature_comfort(weather['temperature'])
        
        # Combine all context
        complete_context = {
            'weather': weather,
            'daily_context': daily_context,
            'comfort_analysis': comfort_analysis,
            'user_profile_summary': {
                'name': self.user_profile.get('name', 'User'),
                'location': self.user_profile.get('location', {}),
                'style_preferences': self.user_profile.get('style_preferences', []),
                'color_season': self.user_profile.get('color_analysis', {}).get('season_type', 'unknown')
            },
            'collection_timestamp': datetime.now().isoformat()
        }
        
        return complete_context
    
    def save_context(self, context: Dict, output_path: str = "daily_context.json"):
        """
        Save collected context to a JSON file.
        
        Args:
            context: Context dictionary to save
            output_path: Path to output JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=2, ensure_ascii=False)
        print(f"\n✓ 情境資料已儲存至: {output_path}")
    
    def print_context_summary(self, context: Dict):
        """
        Print a human-readable summary of collected context.
        
        Args:
            context: Context dictionary to summarize
        """
        print("\n" + "="*60)
        print("📊 情境資訊摘要")
        print("="*60)
        
        # Weather
        weather = context.get('weather', {})
        print(f"\n🌤️  天氣狀況")
        print(f"  📍 地點: {weather.get('city', 'N/A')}")
        print(f"  🌡️  溫度: {weather.get('temperature', 'N/A')}°C (體感 {weather.get('feels_like', 'N/A')}°C)")
        print(f"  💧 濕度: {weather.get('humidity', 'N/A')}%")
        print(f"  ☁️  天氣: {weather.get('weather_description', 'N/A')}")
        
        # Comfort Analysis
        comfort = context.get('comfort_analysis', {})
        print(f"\n🌡️  舒適度分析")
        print(f"  舒適度: {comfort.get('comfort_level', 'N/A')}")
        print(f"  建議層次: {comfort.get('layers_needed', 'N/A')}")
        if comfort.get('recommendations'):
            print("  💡 穿搭建議:")
            for rec in comfort['recommendations']:
                print(f"     • {rec}")
        
        # Daily Context
        daily = context.get('daily_context', {})
        print(f"\n📋 今日情境")
        print(f"  🎯 場合: {daily.get('occasion', 'N/A')}")
        print(f"  👔 正式程度: {daily.get('formality_name', 'N/A')}")
        
        if daily.get('has_dress_code'):
            print(f"  📜 著裝要求: {daily.get('dress_code', 'N/A')}")
        
        print(f"  ✨ 風格偏好: {daily.get('style_preference', 'N/A')}")
        print(f"  📅 活動: {', '.join(daily.get('activities', ['N/A']))}")
        print(f"  ⏰ 時長: {daily.get('duration_hours', 'N/A')} 小時")
        print(f"  🌳 戶外時間: {daily.get('outdoor_time', 'N/A')} 小時")
        
        if daily.get('color_preference'):
            print(f"  🎨 偏好顏色: {', '.join(daily['color_preference'])}")
        
        if daily.get('avoid_colors'):
            print(f"  🚫 避免顏色: {', '.join(daily['avoid_colors'])}")
        
        if daily.get('special_requirements'):
            print(f"  💡 特殊需求: {daily['special_requirements']}")
        
        print("\n" + "="*60 + "\n")


def main():
    """
    Example usage of Context Collector Agent.
    """
    # Example with user profile
    example_profile = {
        'name': '小美',
        'location': {'city': 'Taipei', 'country_code': 'TW'},
        'style_preferences': ['韓系', '極簡風'],
        'color_analysis': {
            'season_type': 'summer',
            'palette': {
                'best_colors': ['soft pink', 'lavender', 'powder blue', 'cool gray']
            }
        },
        'temperature_sensitivity': '怕冷',
        'common_occasions': ['上班', '休閒外出']
    }
    
    # Initialize agent
    agent = ContextCollectorAgent(user_profile=example_profile)
    
    # Collect complete context
    context = agent.collect_complete_context(ask_questions=True)
    
    # Print summary
    agent.print_context_summary(context)
    
    # Save context
    agent.save_context(context, "daily_context.json")


if __name__ == "__main__":
    main()
