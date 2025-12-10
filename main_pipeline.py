"""
Main Pipeline - Complete Outfit Recommendation System
Integrates all steps:
1. Catalog Builder: Generate embeddings and descriptions
2. Context Collector: Collect user profile and daily context
3. Outfit Planner: Recommend outfits
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict


def check_dependencies():
    """Check if all required files exist."""
    required_files = {
        'outfit_descriptions.json': 'Outfit descriptions (from step 1)',
        'outfit_embeddings.npy': 'Outfit embeddings (from step 1)',
        'catalog_index.json': 'Catalog index (from step 1)',
        'generate_embeddings.py': 'Step 1a: Generate embeddings',
        'generate_outfit_descriptions.py': 'Step 1b: Generate descriptions',
        'user_profile_manager.py': 'Step 2a: User profile manager',
        'context_collector_agent.py': 'Step 2b: Context collector',
        'outfit_planner.py': 'Step 3: Outfit planner',
        'standardize_categories.py': 'Data standardization (category mapping)'
    }
    
    print("\n" + "="*60)
    print("🔍 依賴檢查")
    print("="*60)
    
    missing = []
    for filename, description in required_files.items():
        if os.path.exists(filename):
            print(f"✓ {filename:<40} {description}")
        else:
            print(f"✗ {filename:<40} ⚠️  {description}")
            missing.append(filename)
    
    return len(missing) == 0, missing


def run_step_1_catalog_builder():
    """
    Step 1: Catalog Builder
    Generate embeddings and descriptions for all outfits.
    """
    print("\n" + "="*60)
    print("📚 第 1 步: 衣服目錄前處理 (Catalog Builder)")
    print("="*60)
    
    # Check if embeddings and descriptions already exist
    embeddings_exist = os.path.exists('outfit_embeddings.npy')
    descriptions_exist = os.path.exists('outfit_descriptions.json')
    catalog_exist = os.path.exists('catalog_index.json')
    
    if embeddings_exist and descriptions_exist and catalog_exist:
        print("\n✓ 衣服目錄資料已存在，跳過生成步驟")
        print("  - outfit_embeddings.npy")
        print("  - outfit_descriptions.json")
        print("  - catalog_index.json")
        return True
    
    print("\n執行衣服目錄前處理...")
    
    # Step 1a: Generate embeddings
    if not embeddings_exist or not catalog_exist:
        print("\n[1a] 正在生成衣服 embeddings...")
        try:
            from generate_embeddings import generate_clip_embeddings
            outfits_folder = os.path.join(os.path.dirname(__file__), "outfits")
            output_file = os.path.join(os.path.dirname(__file__), "outfit_embeddings.npy")
            catalog_index_file = os.path.join(os.path.dirname(__file__), "catalog_index.json")
            
            generate_clip_embeddings(outfits_folder, output_file, catalog_index_file)
            print("✓ Embeddings 生成完成")
        except Exception as e:
            print(f"✗ Embeddings 生成失敗: {e}")
            return False
    else:
        print("\n[1a] ✓ 衣服 embeddings 已存在")
    
    # Step 1b: Generate descriptions
    if not descriptions_exist:
        print("\n[1b] 正在生成衣服文字描述...")
        try:
            from generate_outfit_descriptions import generate_outfit_descriptions
            outfits_folder = os.path.join(os.path.dirname(__file__), "outfits")
            output_file = os.path.join(os.path.dirname(__file__), "outfit_descriptions.json")
            
            generate_outfit_descriptions(outfits_folder, output_file)
            print("✓ 文字描述生成完成")
        except Exception as e:
            print(f"✗ 文字描述生成失敗: {e}")
            return False
    else:
        print("\n[1b] ✓ 衣服文字描述已存在")
    
    print("\n✓ 第 1 步完成：衣服目錄前處理")
    return True


def run_standardize_categories():
    """
    Run category standardization to normalize item categories.
    This produces `catalog_standardized.json` used to improve recommendation quality.
    """
    print("\n" + "="*60)
    print("🔧 執行分類標準化 (standardize_categories)")
    print("="*60)
    try:
        import standardize_categories
        standardize_categories.standardize_data()
        print("✓ 分類標準化完成 (catalog_standardized.json)")
        return True
    except Exception as e:
        print(f"✗ 分類標準化失敗: {e}")
        return False


def run_step_2_context_collector():
    """
    Step 2: Context Collector
    Collect user profile and daily context information.
    """
    print("\n" + "="*60)
    print("📋 第 2 步: 情境收集 (Context Collector)")
    print("="*60)
    
    # Check if profile exists
    profile_exists = os.path.exists('user_profile.json')
    
    # Step 2a: User Profile
    print("\n[2a] 使用者檔案管理...")
    try:
        from user_profile_manager import UserProfileManager
        
        manager = UserProfileManager()
        
        if profile_exists:
            profile = manager.load_profile()
            print("✓ 已載入現有使用者檔案")
        else:
            print("✗ 未找到使用者檔案")
            print("\n是否要建立新的使用者檔案？")
            response = input("(y/n, 預設 y): ").strip().lower() or 'y'
            
            if response == 'y':
                profile = manager.run_first_time_setup()
                manager.save_profile(profile)
                print("✓ 使用者檔案建立完成")
            else:
                print("⚠️  跳過使用者檔案建立")
                profile = None
    except Exception as e:
        print(f"✗ 使用者檔案步驟失敗: {e}")
        profile = None
    
    # Step 2b: Context Collection
    print("\n[2b] 正在收集每日情境資訊...")
    try:
        from context_collector_agent import ContextCollectorAgent
        
        # Use loaded profile if available, otherwise use defaults
        if profile:
            agent = ContextCollectorAgent(user_profile=profile)
        else:
            agent = ContextCollectorAgent()
        
        context = agent.collect_complete_context(ask_questions=True)
        
        # Save context
        agent.save_context(context, "daily_context.json")
        print("✓ 情境資訊收集完成")
        
        return context
    except Exception as e:
        print(f"✗ 情境收集失敗: {e}")
        
        # Try to load existing context
        if os.path.exists('daily_context.json'):
            print("\n載入現有的每日情境資訊...")
            with open('daily_context.json', 'r', encoding='utf-8') as f:
                context = json.load(f)
            return context
        else:
            return None


def run_step_3_outfit_planner(context: Dict):
    """
    Step 3: Outfit Planner
    Generate outfit recommendations based on context.
    
    Args:
        context: Context dictionary from step 2
    """
    print("\n" + "="*60)
    print("👕 第 3 步: 穿搭推薦 (Outfit Planner)")
    print("="*60)
    
    try:
        from outfit_planner import OutfitPlanner
        
        print("\n初始化穿搭推薦系統...")
        planner = OutfitPlanner()
        
        if context:
            print("\n根據收集的情境資訊進行推薦...")
            recommendations = planner.recommend_complete_outfit(context)
        else:
            print("\n使用預設情境進行推薦...")
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
                    'color_preference': None,
                    'avoid_colors': []
                },
                'comfort_analysis': {
                    'comfort_level': 'comfortable',
                    'layers_needed': 'light',
                    'recommendations': ['輕薄外套即可', '可穿長袖或短袖']
                },
                'user_profile_summary': {
                    'name': '使用者',
                    'color_season': 'summer',
                    'style_preferences': ['休閒風']
                }
            }
            recommendations = planner.recommend_complete_outfit(example_context)
        
        # Save recommendations
        planner.save_recommendation(recommendations)
        
        print("\n✓ 第 3 步完成：穿搭推薦")
        return recommendations
        
    except Exception as e:
        print(f"✗ 穿搭推薦失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_complete_pipeline(skip_user_input: bool = False):
    """
    Run the complete pipeline from step 1 to step 3.
    
    Args:
        skip_user_input: If True, skip user input and use defaults
    """
    print("\n" + "="*70)
    print("🎯 智能衣櫥推薦系統 - 完整管道")
    print("="*70)
    print("\n步驟 1: 衣服目錄前處理 (Catalog Builder)")
    print("步驟 2: 情境資訊收集 (Context Collector)")
    print("步驟 3: 穿搭推薦 (Outfit Planner)")
    
    # Check dependencies
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        print(f"\n✗ 缺少必要檔案: {', '.join(missing)}")
        return False
    
    # Step 1: Catalog Builder
    if not run_step_1_catalog_builder():
        print("\n✗ 步驟 1 失敗")
        return False
    # After Step 1: run category standardization to normalize categories
    try:
        run_standardize_categories()
    except Exception:
        # non-fatal: continue pipeline even if standardization fails
        print("⚠️  分類標準化步驟發生錯誤，將繼續執行後續步驟")
    
    # Step 2: Context Collector
    if skip_user_input:
        print("\n⏭️  跳過用戶輸入，使用預設值")
        context = None
    else:
        context = run_step_2_context_collector()
    
    # Step 3: Outfit Planner
    run_step_3_outfit_planner(context)
    
    # Summary
    print("\n" + "="*70)
    print("✓ 完整管道執行完成!")
    print("="*70)
    print("\n📁 生成的檔案:")
    print("  - outfit_recommendation.json: 穿搭推薦結果")
    print("  - daily_context.json: 每日情境資訊")
    print("  - user_profile.json: 使用者檔案")
    print("\n感謝使用智能衣櫥推薦系統!")
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="智能衣櫥推薦系統 - 完整管道",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python main_pipeline.py              # 執行完整管道
  python main_pipeline.py --quick      # 快速模式 (跳過用戶輸入)
  python main_pipeline.py --step 1     # 只執行第 1 步
  python main_pipeline.py --step 2     # 只執行第 2 步
  python main_pipeline.py --step 3     # 只執行第 3 步
        """
    )
    
    parser.add_argument(
        '--step',
        type=int,
        choices=[1, 2, 3],
        help='只執行指定的步驟'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='快速模式：跳過用戶輸入，使用預設值'
    )
    
    args = parser.parse_args()
    
    try:
        if args.step:
            # Run specific step
            if args.step == 1:
                run_step_1_catalog_builder()
                # run standardization after step 1 for better downstream matching
                run_standardize_categories()
            elif args.step == 2:
                context = run_step_2_context_collector()
            elif args.step == 3:
                # For step 3, try to load existing context
                if os.path.exists('daily_context.json'):
                    with open('daily_context.json', 'r', encoding='utf-8') as f:
                        context = json.load(f)
                else:
                    context = None
                run_step_3_outfit_planner(context)
        else:
            # Run complete pipeline
            run_complete_pipeline(skip_user_input=args.quick)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  使用者中斷執行")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
