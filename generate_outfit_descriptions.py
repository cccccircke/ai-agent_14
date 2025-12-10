import os
import json
import torch
from pathlib import Path
from PIL import Image
import tqdm
from transformers import AutoProcessor, LlavaForConditionalGeneration

def generate_outfit_descriptions(folder_path, output_path):
    """
    Generate detailed outfit descriptions using LLaVA Vision Language Model.
    Outputs a JSON file mapping image filenames to outfit details.
    """
    # Device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Load LLaVA model
    print("Loading LLaVA Vision Language Model...")
    model_id = "llava-hf/llava-1.5-7b-hf"
    processor = AutoProcessor.from_pretrained(model_id)
    model = LlavaForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None
    )
    
    if device == "cpu":
        model = model.to(device)
    
    # Get all image files
    folder = Path(folder_path)
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff'}
    
    image_files = []
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in image_extensions:
            image_files.append(file)
    
    # Sort by numeric filename
    def sort_key(f):
        try:
            return int(f.stem)
        except ValueError:
            return float('inf')
    
    image_files.sort(key=sort_key)
    
    print(f"Found {len(image_files)} images")
    
    # Prompt for detailed outfit analysis
    analysis_prompt = """Analyze this outfit image in detail and provide structured information about the clothing item/outfit shown. 
    
    Please identify and describe:
    1. Type (Upper for tops/shirts/jackets, Lower for pants/skirts/shorts, Dress for one-piece outfits/dresses)
    2. Category (e.g., Outerwear, Top, Bottom, Dress, Accessories, Footwear)
    3. Subcategory (e.g., Overcoat, T-shirt, Jeans, Sneakers)
    4. Primary color
    5. Secondary colors (if any)
    6. Pattern (Solid, Striped, Plaid, Floral, etc.)
    7. Material/Fabric type (Cotton, Wool, Silk, Leather, etc.)
    8. Sleeve length (for tops/outerwear)
    9. Overall length/fit
    10. Style aesthetic (Business Casual, Streetwear, Minimalist, Vintage, etc.)
    11. Fit/Silhouette (Fitted, Relaxed, Oversized, etc.)
    12. A complete 2-3 sentence description of the outfit
    
    Format your response as follows:
    TYPE: [Upper/Lower/Dress]
    CATEGORY: [category]
    SUBCATEGORY: [subcategory]
    COLOR_PRIMARY: [primary color]
    COLOR_SECONDARY: [secondary colors or N/A]
    PATTERN: [pattern type]
    MATERIAL: [material/fabric]
    SLEEVE_LENGTH: [sleeve length or N/A]
    LENGTH: [length/fit description]
    STYLE_AESTHETIC: [aesthetic style]
    FIT_SILHOUETTE: [fit type]
    COMPLETE_DESCRIPTION: [2-3 sentence description]"""
    
    # Generate descriptions
    outfit_descriptions = {}
    
    for image_path in tqdm.tqdm(image_files):
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            
            # Prepare inputs
            inputs = processor(images=image, text=analysis_prompt, return_tensors="pt")
            
            # Move to device
            for key in inputs:
                if isinstance(inputs[key], torch.Tensor):
                    inputs[key] = inputs[key].to(device)
            
            # Generate response
            with torch.no_grad():
                output_ids = model.generate(
                    **inputs,
                    max_new_tokens=300,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9
                )
            
            # Decode response
            response = processor.decode(output_ids[0], skip_special_tokens=True)
            
            # Parse the response
            outfit_data = parse_outfit_response(response)
            outfit_descriptions[image_path.name] = outfit_data
            
        except Exception as e:
            print(f"Error processing {image_path.name}: {e}")
            # Add error entry
            outfit_descriptions[image_path.name] = {
                "type": "Unknown",
                "category": "Unknown",
                "subcategory": "Unknown",
                "color_primary": "Unknown",
                "color_secondary": "N/A",
                "pattern": "Unknown",
                "material": "Unknown",
                "sleeve_length": "N/A",
                "length": "Unknown",
                "style_aesthetic": "Unknown",
                "fit_silhouette": "Unknown",
                "complete_description": f"Error processing image: {str(e)}",
                "error": True
            }
    
    # Save to JSON file
    with open(output_path, 'w') as f:
        json.dump(outfit_descriptions, f, indent=2)
    
    print(f"\nSaved outfit descriptions to: {output_path}")
    print(f"Successfully processed {len(outfit_descriptions)} images")
    
    # Print sample entries
    print(f"\nSample descriptions (first 2 items):")
    for filename, data in list(outfit_descriptions.items())[:2]:
        print(f"\n{filename}:")
        print(f"  Category: {data.get('category', 'Unknown')}")
        print(f"  Color: {data.get('color_primary', 'Unknown')}")
        print(f"  Style: {data.get('style_aesthetic', 'Unknown')}")

def parse_outfit_response(response):
    """
    Parse the LLaVA response into structured outfit data.
    """
    lines = response.split('\n')
    outfit_data = {
        "type": "Unknown",
        "category": "Unknown",
        "subcategory": "Unknown",
        "color_primary": "Unknown",
        "color_secondary": "N/A",
        "pattern": "Unknown",
        "material": "Unknown",
        "sleeve_length": "N/A",
        "length": "Unknown",
        "style_aesthetic": "Unknown",
        "fit_silhouette": "Unknown",
        "complete_description": ""
    }
    
    # Parse key-value pairs from response
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().upper()
            value = value.strip()
            
            # Map to outfit data keys
            if key == "TYPE":
                outfit_data["type"] = value
            elif key == "CATEGORY":
                outfit_data["category"] = value
            elif key == "SUBCATEGORY":
                outfit_data["subcategory"] = value
            elif key == "COLOR_PRIMARY":
                outfit_data["color_primary"] = value
            elif key == "COLOR_SECONDARY":
                outfit_data["color_secondary"] = value if value else "N/A"
            elif key == "PATTERN":
                outfit_data["pattern"] = value
            elif key == "MATERIAL":
                outfit_data["material"] = value
            elif key == "SLEEVE_LENGTH":
                outfit_data["sleeve_length"] = value if value else "N/A"
            elif key == "LENGTH":
                outfit_data["length"] = value
            elif key == "STYLE_AESTHETIC":
                outfit_data["style_aesthetic"] = value
            elif key == "FIT_SILHOUETTE":
                outfit_data["fit_silhouette"] = value
            elif key == "COMPLETE_DESCRIPTION":
                outfit_data["complete_description"] = value
    
    return outfit_data


if __name__ == "__main__":
    # Set paths
    outfits_folder = os.path.join(os.path.dirname(__file__), "outfits")
    output_file = os.path.join(os.path.dirname(__file__), "outfit_descriptions.json")
    
    # Check if folder exists
    if not os.path.exists(outfits_folder):
        print(f"Error: Folder '{outfits_folder}' not found!")
    else:
        generate_outfit_descriptions(outfits_folder, output_file)
