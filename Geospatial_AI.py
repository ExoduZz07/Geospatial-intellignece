import cv2
import numpy as np
import rasterio
import os

def apply_color_and_context(original_tif_path, ai_mask_path):
    print("🎨 Initializing Spectral & Contextual Engine...")
    
    # --- 1. Setup Output Directory ---
    output_dir = "Final_Outputs"
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(original_tif_path).replace(".tif", "_Extraction.tif")
    output_path = os.path.join(output_dir, base_name)

    # --- 2. Load the Raw AI Mask ---
    with rasterio.open(ai_mask_path) as src:
        meta = src.meta.copy()
        mask_data = src.read(1).astype(np.uint8) # Ensure format is safe for OpenCV

    # =====================================================================
    # 🧹 STEP 3: THE GRID DESTROYER (SEAM ARTIFACT CLEANUP)
    # =====================================================================
    # A 5x5 Median Filter instantly deletes 1-pixel thick border lines
    # while preserving solid geometry like buildings and lakes.
    mask_data = cv2.medianBlur(mask_data, 5)

    # =====================================================================
    # 🧠 STEP 4: GEOMETRIC FILTERING (THE ROAD FIX)
    # =====================================================================
    # Isolate Class 6 (Roads)
    road_mask = (mask_data == 6).astype(np.uint8)

    # Destroy the massive farms (anything wider than 25 pixels)
    kernel_size = 25 
    tophat_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    thin_roads = cv2.morphologyEx(road_mask, cv2.MORPH_TOPHAT, tophat_kernel)

    # Smooth and connect the remaining true roads
    smooth_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    sleek_roads = cv2.morphologyEx(thin_roads, cv2.MORPH_CLOSE, smooth_kernel)

    # Erase old roads, paste the sleek roads
    mask_data[mask_data == 6] = 0 
    mask_data[sleek_roads == 1] = 6

    # =====================================================================
    # 💾 SAVE & EXPORT
    # =====================================================================
    meta.update({"compress": "lzw"})
    with rasterio.open(output_path, 'w', **meta) as dst:
        dst.write(mask_data, 1)

    print(f"✅ Geometric constraints applied. Saved to: {output_path}")
    return output_path
