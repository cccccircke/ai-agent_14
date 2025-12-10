import os
import json
import numpy as np
from pathlib import Path
import clip
import torch
from PIL import Image
import tqdm

def generate_clip_embeddings(folder_path, output_path, catalog_index_path=None):
    """
    Generate CLIP embeddings (512-dim) for all images in a folder.
    Saves embeddings to a single .npy file.
    """
    # Device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Load CLIP model
    print("Loading CLIP model...")
    model, preprocess = clip.load("ViT-B/32", device=device)
    
    # Get all image files
    folder = Path(folder_path)
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff'}
    
    image_files = []
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in image_extensions:
            image_files.append(file)
    
    # Sort to match the order from rename_images.py (by numeric filename)
    def sort_key(f):
        try:
            # Try to extract numeric part from filename (e.g., "1.jpg" -> 1)
            return int(f.stem)
        except ValueError:
            # Fall back to filename if not numeric
            return float('inf')
    
    image_files.sort(key=sort_key)
    
    print(f"Found {len(image_files)} images")
    
    # Generate embeddings
    embeddings = []
    
    with torch.no_grad():
        for image_path in tqdm.tqdm(image_files):
            try:
                # Load and preprocess image
                image = Image.open(image_path).convert('RGB')
                image_input = preprocess(image).unsqueeze(0).to(device)
                
                # Get embedding
                embedding = model.encode_image(image_input)
                
                # Convert to numpy and append
                embeddings.append(embedding.cpu().numpy().flatten())
                
            except Exception as e:
                print(f"Error processing {image_path.name}: {e}")
    
    # Stack all embeddings into a single array
    embeddings_array = np.vstack(embeddings)
    
    print(f"\nEmbeddings shape: {embeddings_array.shape}")
    print(f"Dimension per image: {embeddings_array.shape[1]}")
    
    # Save to .npy file
    np.save(output_path, embeddings_array)
    print(f"\nSaved embeddings to: {output_path}")
    
    # Create and save catalog index for quick lookup
    if catalog_index_path is None:
        catalog_index_path = output_path.replace('.npy', '_index.json')
    
    catalog_index = {
        file.name: {
            "filename": file.name,
            "embedding_index": idx,
            "extension": file.suffix
        }
        for idx, file in enumerate(image_files)
    }
    
    with open(catalog_index_path, 'w') as f:
        json.dump(catalog_index, f, indent=2)
    
    print(f"Saved catalog index to: {catalog_index_path}")
    
    # Print summary
    print(f"\nSuccessfully generated embeddings for {len(embeddings_array)} images")
    print(f"Each embedding has 512 dimensions")
    print(f"Total file size: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
    
    # Print sample catalog entries
    print(f"\nCatalog Index Sample (first 3 items):")
    for i, (key, value) in enumerate(list(catalog_index.items())[:3]):
        print(f"  {key}: embedding_index={value['embedding_index']}, filename={value['filename']}")

if __name__ == "__main__":
    # Set paths
    outfits_folder = os.path.join(os.path.dirname(__file__), "outfits")
    output_file = os.path.join(os.path.dirname(__file__), "outfit_embeddings.npy")
    catalog_index_file = os.path.join(os.path.dirname(__file__), "catalog_index.json")
    
    # Check if folder exists
    if not os.path.exists(outfits_folder):
        print(f"Error: Folder '{outfits_folder}' not found!")
    else:
        generate_clip_embeddings(outfits_folder, output_file, catalog_index_file)
