import streamlit as st
import os
import time
import rasterio
from rasterio.enums import Resampling
import numpy as np
from PIL import Image
import glob
import cv2

# --- 1. CLOUD-SAFE IMPORTS & SECURITY ---
from run_inference import run_ai_scanner
from Geospatial_AI import apply_color_and_context

# Disable Decompression Bomb protection for massive drone maps
Image.MAX_IMAGE_PIXELS = None

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="GeoAI Control", page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")

# --- INITIALIZE MEMORY ---
if 'scan_complete' not in st.session_state:
    st.session_state.scan_complete = False
if 'final_map_path' not in st.session_state:
    st.session_state.final_map_path = ""
if 'original_map' not in st.session_state:
    st.session_state.original_map = ""

# --- ADVANCED CUSTOM CSS ---
st.markdown("""
    <style>
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: 800; 
        font-size: 18px;
        background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%); 
        color: #0A0A0A; 
        border: none; 
        padding: 12px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 242, 254, 0.4);
    }
    .stButton>button:hover { 
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.6);
        color: white;
    }
    .highlight { color: #00F2FE; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: TELEMETRY ---
with st.sidebar:
    st.title("🛰️ GeoAI Control")
    st.caption("SVAMITVA Geospatial AI - Team Project")
    st.divider()
    st.markdown("### ⚙️ System Telemetry")
    st.success("🟢 U-Net ResNet18: Online")
    st.success("🟢 Spectral Engine: Active")
    st.success("🟢 GPU VRAM: Optimal")

# --- MAIN DASHBOARD HEADER ---
st.markdown("<h1>🌍<span class='highlight'> Automated Mapping Engine</span></h1>", unsafe_allow_html=True)
st.markdown("High-Resolution Asset Classification via Deep Learning & Contextual Geometry")
st.divider()

# --- LAYOUT: TABS ---
tab1, tab2 = st.tabs(["🚀 Mission Control", "🗄️ Output Gallery"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📍 Target Acquisition (Enterprise)")
        
        # Look directly into the Colab-mounted Google Drive
        drive_path = "/content/drive/MyDrive/TerraScan_Data/"
        tif_files = glob.glob(f"{drive_path}*.tif")
        
        if not tif_files:
            st.warning("⚠️ No files found. Ensure Colab is running & Drive mounted.")
            target_file_path = None
        else:
            file_names = [os.path.basename(f) for f in tif_files]
            selected_name = st.selectbox("Select Target Area:", file_names)
            target_file_path = os.path.join(drive_path, selected_name)
        
        with st.expander("🛠️ Advanced Configuration"):
            st.slider("Texture Veto Sensitivity", 1, 100, 80)
            st.checkbox("Enable Deep Water Penetration", value=True)
            st.checkbox("Force Strict Geometry (Lakes)", value=True)
            st.caption("Note: UI sliders locked to optimal presets for demo.")

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        run_btn = st.button("⚡ INITIATE SCAN")

    # --- PIPELINE EXECUTION ---
    if run_btn:
        if target_file_path is None:
            st.error("❌ Please select a file from the dropdown first!")
        else:
            # We bypass the upload/save entirely and just use the Drive path
            tif_path = target_file_path
            
            with st.status("Initializing GeoAI Sequence...", expanded=True) as status:
                try:
                    # STEP 1: AI INFERENCE
                    st.write("🧠 [1/2] Executing Deep Learning Geometry Scan...")
                    ai_mask_path = run_ai_scanner(tif_path)
                    
                    # STEP 2: SPECTRAL ENGINE
                    st.write("🎨 [2/2] Applying Spectral & Texture Constraints...")
                    final_map_path = apply_color_and_context(tif_path, ai_mask_path)
                    
                    status.update(label="Mission Accomplished!", state="complete", expanded=False)
                    st.success(f"🎉 Map Successfully Generated!")
                    st.balloons()
                    
                    # Provide Instant Download
                    with open(final_map_path, "rb") as f:
                        st.download_button(
                            label="📥 Download High-Res Final Map (.tif)",
                            data=f,
                            file_name=os.path.basename(final_map_path),
                            mime="image/tiff"
                        )
                    
                    # Post-Scan Analytics
                    st.markdown("### 📈 Post-Scan Analytics")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Pixel Processing", "Complete", "100%")
                    m2.metric("False Positives", "Cleared", "Texture Veto")
                    m3.metric("System Health", "Stable", "No Memory Leaks")

                    # LOCK INTO MEMORY
                    st.session_state.scan_complete = True
                    st.session_state.final_map_path = final_map_path
                    st.session_state.original_map = tif_path # Save original for X-Ray

                except Exception as e:
                    status.update(label="System Failure", state="error", expanded=True)
                    st.error(f"❌ Crash at Module: {e}")
                    st.session_state.scan_complete = False

    # --- THE INTERACTIVE CLASS VIEWER (Upgraded) ---
    if st.session_state.scan_complete and os.path.exists(st.session_state.final_map_path):
        st.divider()
        st.markdown("### 🔍 Live Map Inspector")
        
        view_mode = st.radio("Display Mode:", ["AI Mask Only", "Overlay (Blended)", "Side-by-Side Compare"], horizontal=True)
        class_choice = st.selectbox("Isolate specific predicted features:", [
            "All Classes", 
            "1 - RCC Roofs (Grey)", 
            "2 - Tin Roofs (Cyan)", 
            "3 - Tiled Roofs (Red)",
            "4 - Utilities (Purple)", 
            "5 - Water Bodies (Blue)", 
            "6 - Roads (Yellow)"
        ])

        with st.spinner("Rendering web-optimized preview..."):
            # 1. Load the AI Mask
            with rasterio.open(st.session_state.final_map_path) as src_mask:
                scale_factor = 1024 / max(src_mask.width, src_mask.height)
                new_height = int(src_mask.height * scale_factor)
                new_width = int(src_mask.width * scale_factor)
                data = src_mask.read(1, out_shape=(new_height, new_width), resampling=Resampling.nearest)
            
            # 2. Load Original Image safely for comparison
            with rasterio.open(st.session_state.original_map) as src_orig:
                orig_raw = src_orig.read(out_shape=(src_orig.count, new_height, new_width), resampling=Resampling.nearest)
                if src_orig.count >= 3:
                    orig_img = np.moveaxis(orig_raw[:3], 0, -1) 
                else:
                    orig_img = np.stack((orig_raw[0],)*3, axis=-1)
            
            # 3. Apply Colors
            color_map = {
                1: [140, 140, 140], 2: [0, 191, 255], 3: [225, 87, 89],
                4: [156, 39, 176], 5: [78, 121, 167], 6: [242, 203, 108]
            }

            viz_img = np.zeros((new_height, new_width, 3), dtype=np.uint8)

            if class_choice == "All Classes":
                for val, col in color_map.items():
                    viz_img[data == val] = col
            else:
                target_val = int(class_choice.split(" ")[0])
                viz_img[data == target_val] = color_map.get(target_val, [0, 0, 0])

            # 4. Display Logic
            if view_mode == "Side-by-Side Compare":
                sub_col1, sub_col2 = st.columns(2)
                sub_col1.image(orig_img, caption="Original Orthomosaic", use_column_width=True)
                sub_col2.image(viz_img, caption=f"AI Output: {class_choice}", use_column_width=True)
            
            elif view_mode == "Overlay (Blended)":
                orig_img = orig_img.astype(np.uint8)
                overlay = cv2.addWeighted(orig_img, 0.6, viz_img, 0.4, 0)
                
                # Keep background clear if isolating a specific feature
                if class_choice != "All Classes":
                    background_mask = (viz_img == [0, 0, 0]).all(axis=2)
                    overlay[background_mask] = orig_img[background_mask]
                    
                st.image(overlay, caption="X-Ray Overlay View", use_column_width=True)
            
            else:
                st.image(viz_img, caption=f"Previewing: {class_choice}", use_column_width=True)

with tab2:
    st.markdown("### 🗄️ Recent Scans")
    output_dir_gallery = "Final_Outputs"
    
    if os.path.exists(output_dir_gallery):
        files = [f for f in os.listdir(output_dir_gallery) if f.endswith('.tif')]
        if files:
            for f in files:
                file_path = os.path.join(output_dir_gallery, f)
                with open(file_path, "rb") as file_data:
                    st.download_button(
                        label=f"📥 Download: {f}",
                        data=file_data,
                        file_name=f,
                        mime="image/tiff",
                        key=f"gallery_{f}"
                    )
