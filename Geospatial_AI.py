import cv2
import numpy as np
import rasterio
import os

def apply_color_and_context(original_tif_path, ai_mask_path):
    """
    Applies geometric and morphological constraints to clean up AI hallucinations.
    Specifically targets Class 6 (Roads) to ensure they are narrow and sleek,
    removing massive farm/field blobs caused by spectral confusion.
    """
    print("🎨 Initializing Spectral & Contextual Engine...")
    
    # --- 1. Setup Output Directory ---
    output_dir = "Final_Outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate a clean output filename based on the original image
    base_name = os.path.basename(original_tif_path).replace(".tif", "_Extraction.tif")
    output_path = os.path.join(output_dir, base_name)

    # --- 2. Load the Raw AI Mask ---
    with rasterio.open(ai_mask_path) as src:
        meta = src.meta.copy()
        mask_data = src.read(1)

    # =====================================================================
    # 🧠 GEOMETRIC FILTERING (THE ROAD FIX)
    # =====================================================================

    # Isolate Class 6 (Roads) into a binary mask (1 for road, 0 for background)
    road_mask = (mask_data == 6).astype(np.uint8)

    # --- STEP A: The Top-Hat Transform (Destroy the Farms) ---
    # A 25x25 kernel represents the maximum thickness of a real road.
    # Anything wider/larger than this box gets deleted.
    # If it erases real roads, increase this number. If farms survive, decrease it.
    kernel_size = 25 
    tophat_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    thin_roads = cv2.morphologyEx(road_mask, cv2.MORPH_TOPHAT, tophat_kernel)

    # --- STEP B: The Smoothing Transform (Connect the Lines) ---
    # The Top-Hat can leave roads looking a bit jagged.
    # We use a closing operation to smooth the edges and bridge small gaps.
    smooth_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    sleek_roads = cv2.morphologyEx(thin_roads, cv2.MORPH_CLOSE, smooth_kernel)

    # --- STEP C: Reconstruct the Master Map ---
    # 1. Erase ALL the old, bad roads (the giant yellow fields)
    mask_data[mask_data == 6] = 0 
    
    # 2. Paste ONLY our newly filtered, sleek roads back onto the map
    mask_data[sleek_roads == 1] = 6

    # =====================================================================
    # 💾 SAVE & EXPORT
    # =====================================================================
    
    # Compress the output to save space
    meta.update({"compress": "lzw"})
    
    with rasterio.open(output_path, 'w', **meta) as dst:
        dst.write(mask_data, 1)

    print(f"✅ Geometric constraints applied. Saved to: {output_path}")
    return output_path
