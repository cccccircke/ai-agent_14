# BDA Final Project (PBL)

## Files:
1. `requirements.txt`
2. `rename_images.py` (utility): sequentially rename each image in `outfits/`
3. `outfits/`: provided clothing pieces (renamed)
4. `generate_embeddings.py`: generates CLIP embeddings of the images in `outfits/`, dimension: 512
5. `outfit_embeddings.npy`: embedding results of outfits in numpy array
6. `catalog_index.json`: mapping of filename in `outfits\` to index in `outfit_embeddings.npy` for fast retrieval
7. `generate_outfit_descriptions.py`: Generate textual descriptions for each outfits in `outfits/`, using LLaVA as backbone VLM model. _use this file for local run_
8. `BDA_Final_Project_generate_outfit_descriptions.ipynb`: Basically `generate_outfit_descriptions.py` converted to python notebook to run in Colab for acceleration with T4 GPU (free tier)
9. `outfit_descriptions.json`: Textual descriptions of each outfits that LLaVa generated (after manually adjusted).
    Fields:
    - category: Upper, Lower, Dress, Set
    - subcategory: More Precise Description of Outfit
    - color_primary, color_secondary
    - pattern
    - material
    - sleeve_length: applies for uppers, dresses, and sets
    - length: Short or Long? Cropped or not?
    - style_aesthetic
    - fit_silhouette
    - complete_description: Short description of the outfit (some doesn't have info on this field)

## Workflow for next steps:
1. Model reads through `outfit_descriptions.json` to filter out / choose appropriate pieces according to user context.
2. For each selected pieces, use `catalog_index.json` to quickly access the piece's embedding in `outfit_embeddings.npy`
3. Because the embeddings are stored in CLIP format, can use any model that can read this format to understand the garment's texture, color, etc from embedding to see which piece goes with which piece.