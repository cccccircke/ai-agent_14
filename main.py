import os
import json
from dotenv import load_dotenv

# 匯入各個模組
# 假設 context_collector_agent.py 裡有一個 ContextCollector 類別
# 假設 user_profile_manager.py 裡有一個 UserProfileManager 類別
try:
    from context_collector_agent import ContextCollector 
    from user_profile_manager import UserProfileManager
except ImportError:
    print("Warning: Step 1.5/2 modules not found. Using mocks if available.")

# 匯入 Step 3 (注意路徑)
from outfit_planner.recommend_v2 import HybridRecommender
from standardize_categories import standardize_data

# 載入環境變數 (OpenAI Key)
load_dotenv()

def main():
    print("=== System Start: AI Outfit Agent ===")

    # 0. 前置檢查與資料準備
    if not os.path.exists("catalog_standardized.json"):
        print("Building standardized catalog...")
        standardize_data()

    # --- Step 1.5 & 2: Context Collection ---
    print("\n--- Step 2: Collecting Context ---")
    # 這裡你需要根據實際的 ContextCollector 實作來呼叫
    # 範例假設：
    # collector = ContextCollector()
    # context_data = collector.get_context() 
    
    # 為了示範，我們先模擬一個從 Context Collector 拿到的資料結構
    # 這應該要替換成真正的 function call
    context_data = {
        "weather": "Sunny, 28°C",
        "location": "Taipei",
        "occasion": "Casual Weekend Date",
        "user_query": "I want something cute and breathable."
    }
    print(f"Context Acquired: {context_data}")

    print("\n--- Step 1.5: User Profile ---")
    # 範例假設：
    # profile_mgr = UserProfileManager()
    # user_style = profile_mgr.get_profile("user_123")
    
    user_style = {
        "personal_color": "Summer Mute",
        "style_preferences": ["Minimalist", "Pastel Colors"],
        "gender": "Female"
    }
    print(f"User Style: {user_style}")

    # --- Step 3: Outfit Planning ---
    print("\n--- Step 3: Planning Outfit ---")
    
    # 初始化 Recommender (它會自動載入 Step 1 的資料)
    recommender = HybridRecommender(base_path=".") 
    
    # 準備輸入給 Step 3 (整合所有 Context)
    step3_input = {
        "user_query": context_data["user_query"],
        "weather": context_data["weather"],
        "occasion": context_data["occasion"],
        "user_profile": user_style,
        "constraints": {} # 可選
    }

    # 執行推薦
    final_decision = recommender.recommend_outfit(step3_input)

    # --- Step 4 Handoff ---
    print("\n=== Final Recommendation (Ready for Presenter) ===")
    print(json.dumps(final_decision, indent=2, ensure_ascii=False))

    # 這裡的 output 就可以直接傳給 Virtual Try-On 模組
    # final_decision['selected_outfit']['id'] -> 圖片檔名
    # final_decision['vton_prompt'] -> 生成提示詞

if __name__ == "__main__":
    main()