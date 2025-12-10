# BDA Final Project - 智能衣櫥穿搭推薦系統

## 🎯 專案概述

這是一個完整的智能衣櫥穿搭推薦系統，包含三個主要步驟：
1. **Catalog Builder**: 衣服前處理 (生成 embeddings 和文字描述)
2. **Context Collector**: 收集外部信息和用戶情境
3. **Outfit Planner**: 根據情境推薦穿搭

## 📁 檔案結構

### 核心檔案

#### 第 1 步: Catalog Builder (衣服前處理)
- `generate_embeddings.py`: 使用 CLIP 生成衣服圖片的 512 維 embedding
- `generate_outfit_descriptions.py`: 使用 LLaVA VLM 生成每件衣服的文字描述
- `outfit_embeddings.npy`: 生成的衣服 embeddings (numpy 陣列)
- `outfit_descriptions.json`: 衣服的詳細文字描述 (JSON)
- `catalog_index.json`: 衣服文件名到 embedding 索引的映射 (快速檢索)

#### 第 2 步: Context Collector (情境收集)
- `user_profile_manager.py`: 管理用戶檔案 (位置、風格偏好、色彩季節分析)
- `context_collector_agent.py`: 收集每日情境 (天氣、場合、正式程度、色彩偏好)

#### 第 3 步: Outfit Planner (穿搭推薦)
- `outfit_planner.py`: 根據情境推薦穿搭的核心邏輯

#### 整合與執行
- `main_pipeline.py`: 完整管道整合入口點，串接第 1-3 步驟
- `INTEGRATION_ANALYSIS.md`: 詳細的整合分析報告

## 🚀 快速開始

### 執行完整管道
```bash
python main_pipeline.py
```

### 快速模式 (跳過用戶輸入)
```bash
python main_pipeline.py --quick
```

### 執行特定步驟
```bash
python main_pipeline.py --step 1  # 衣服前處理
python main_pipeline.py --step 2  # 情境收集
python main_pipeline.py --step 3  # 穿搭推薦
```

## ✅ 整合檢查狀態

- ✅ 步驟 1: 完整 (Catalog Builder)
- ✅ 步驟 2: 完整 (Context Collector) 
- ✅ 步驟 3: 完整 (Outfit Planner)
- ✅ 步驟 1→2: 無直接依賴 (可並行)
- ✅ 步驟 2→3: 完整連接
- ✅ 主程式: 完整整合 (main_pipeline.py)

詳細的整合分析請見 `INTEGRATION_ANALYSIS.md`
