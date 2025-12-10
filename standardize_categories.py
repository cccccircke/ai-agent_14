import json
import os

def standardize_data():
    # 1. 讀取原始描述
    if not os.path.exists('outfit_descriptions.json'):
        print("Error: outfit_descriptions.json not found!")
        return

    with open('outfit_descriptions.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # 2. 定義簡單的關鍵字映射
    mapping = {
        "Upper": ["top", "shirt", "blouse", "sweater", "jacket", "coat", "hoodie", "t-shirt"],
        "Lower": ["pant", "jeans", "trousers", "skirt", "short", "legging"],
        "Dress": ["dress", "gown", "jumpsuit"],
        "Shoe": ["shoe", "sneaker", "boot", "sandal"]
    }

    standardized = {}
    
    for filename, meta in raw_data.items():
        # 取得描述中的類別文字
        cat_text = (meta.get('category', '') + " " + meta.get('subcategory', '')).lower()
        
        # 判斷標準分類
        std_cat = "Accessory" # 預設
        for key, keywords in mapping.items():
            if any(k in cat_text for k in keywords):
                std_cat = key
                break
        
        # 建立新的標準化物件
        standardized[filename] = {
            "id": filename,
            "category": std_cat,
            "description": meta.get('complete_description', ''),
            "original_meta": meta
        }

    # 3. 存檔供 Step 3 使用
    with open('catalog_standardized.json', 'w', encoding='utf-8') as f:
        json.dump(standardized, f, indent=2, ensure_ascii=False)
    
    print(f"Standardization complete. Converted {len(standardized)} items.")

if __name__ == "__main__":
    standardize_data()