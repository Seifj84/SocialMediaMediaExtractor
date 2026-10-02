"""
Streamlit Web UI for OmniMedia Extractor.
Alternative web-based user interface.
"""

import os
import streamlit as st
from media_extractor.core.models import MediaFilter, MediaQuality
from media_extractor.core.config import get_config, save_config
from media_extractor.extractors.manager import ExtractorManager
from media_extractor.utils.file_utils import format_bytes


def run_web_app():
    st.set_page_config(
        page_title="OmniMedia - Social Media Media Extractor",
        page_icon="📥",
        layout="wide",
    )

    st.title("📥 OmniMedia Extractor")
    st.markdown("Download high-definition photos, audios, and videos from Instagram, TikTok, YouTube, X, Reddit, and more.")

    config = get_config()

    col1, col2 = st.columns([2, 1])

    with col1:
        url = st.text_input("🔗 Social Media Post Link", placeholder="https://www.instagram.com/p/...")
        output_dir = st.text_input("📁 Destination Save Directory", value=config.default_output_dir)

    with col2:
        media_filter = st.selectbox(
            "Filter Media",
            options=["All Media", "Photos / Images Only", "Videos Only", "Audio Only"],
            index=0
        )
        quality = st.selectbox(
            "Quality Tier",
            options=["Highest Available (Best)", "1080p High", "720p Medium"],
            index=0
        )

    col_sub, col_jpg = st.columns(2)
    with col_sub:
        subfolder = st.checkbox("Organize in author subfolder", value=config.create_author_subfolder)
    with col_jpg:
        convert_jpg = st.checkbox("Convert WebP images to JPG", value=config.convert_webp_to_jpg)

    filter_map = {
        "All Media": MediaFilter.ALL,
        "Photos / Images Only": MediaFilter.IMAGES_ONLY,
        "Videos Only": MediaFilter.VIDEOS_ONLY,
        "Audio Only": MediaFilter.AUDIO_ONLY,
    }

    quality_map = {
        "Highest Available (Best)": MediaQuality.BEST,
        "1080p High": MediaQuality.HIGH,
        "720p Medium": MediaQuality.MEDIUM,
    }

    if st.button("🚀 Extract & Download Media", type="primary", use_container_width=True):
        if not url.strip():
            st.error("Please enter a valid social media URL.")
            return

        config.create_author_subfolder = subfolder
        config.convert_webp_to_jpg = convert_jpg
        save_config(config)

        os.makedirs(output_dir, exist_ok=True)
        manager = ExtractorManager(config)

        with st.spinner(f"Extracting media from {url}..."):
            result = manager.extract(
                url=url.strip(),
                output_dir=output_dir,
                media_filter=filter_map[media_filter],
                quality=quality_map[quality],
            )

        if result.success and result.downloaded_files:
            st.success(f"Successfully downloaded {len(result.downloaded_files)} file(s) into `{result.target_dir}`!")
            st.subheader("Downloaded Files:")
            for fp in result.downloaded_files:
                sz = format_bytes(os.path.getsize(fp)) if os.path.exists(fp) else ""
                st.write(f"- `{os.path.basename(fp)}` ({sz})")

            if result.metadata_file and os.path.exists(result.metadata_file):
                with open(result.metadata_file, "r", encoding="utf-8") as mf:
                    st.json(mf.read())
        elif result.success and not result.downloaded_files:
            st.warning("Extraction succeeded, but no media matched your filter.")
        else:
            st.error(f"Extraction failed: {result.error_message}")


if __name__ == "__main__":
    run_web_app()
