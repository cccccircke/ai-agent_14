import os
from PIL import Image
from pathlib import Path

def rename_and_convert_images(folder_path):
    """
    Rename all images in the folder to sequential numbers (1.jpg, 2.jpg, etc.)
    and convert non-JPG formats to JPG.
    """
    # Get all image files in the folder
    folder = Path(folder_path)
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff'}
    
    # Get all image files
    image_files = []
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in image_extensions:
            image_files.append(file)
    
    # Sort files by name to ensure consistent ordering
    image_files.sort()
    
    print(f"Found {len(image_files)} images in {folder_path}")
    
    # Create a temporary folder to store processed images
    temp_folder = folder / "temp_renamed"
    temp_folder.mkdir(exist_ok=True)
    
    # Process each image
    for index, image_path in enumerate(image_files, start=1):
        try:
            # Open the image
            img = Image.open(image_path)
            
            # Convert to RGB if necessary (for webp, png with transparency, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as JPG with new sequential name
            new_filename = f"{index}.jpg"
            new_path = temp_folder / new_filename
            img.save(new_path, 'JPEG', quality=95)
            
            print(f"Converted: {image_path.name} -> {new_filename}")
            
        except Exception as e:
            print(f"Error processing {image_path.name}: {e}")
    
    # Remove original files
    for image_path in image_files:
        try:
            image_path.unlink()
            print(f"Deleted original: {image_path.name}")
        except Exception as e:
            print(f"Error deleting {image_path.name}: {e}")
    
    # Move renamed files from temp folder to main folder
    for temp_file in temp_folder.iterdir():
        if temp_file.is_file():
            destination = folder / temp_file.name
            temp_file.rename(destination)
    
    # Remove temp folder
    temp_folder.rmdir()
    
    print(f"\nSuccessfully renamed and converted {len(image_files)} images!")
    print(f"Images are now named: 1.jpg, 2.jpg, ..., {len(image_files)}.jpg")

if __name__ == "__main__":
    # Set the folder path
    outfits_folder = os.path.join(os.path.dirname(__file__), "outfits")
    
    # Check if folder exists
    if not os.path.exists(outfits_folder):
        print(f"Error: Folder '{outfits_folder}' not found!")
    else:
        rename_and_convert_images(outfits_folder)
