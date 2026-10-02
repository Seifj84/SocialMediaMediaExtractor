"""
Streamlit Web UI for OmniMedia Extractor with Live Monitoring & Log Audit.
"""

import os
import sys
import subprocess
import streamlit as st
from media_extractor.core.models import MediaFilter, MediaQuality
from media_extractor.core.config import get_config, save_config
from media_extractor.core.history import get_history_tracker
from media_extractor.core.ffmpeg_finder import find_ffmpeg, get_ffmpeg_version
from media_extractor.extractors.manager import ExtractorManager
from media_extractor.utils.file_utils import format_bytes


def open_in_explorer(path: str):
    """Opens directory in native OS file explorer."""
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
    except Exception:
        pass


def run_web_app():
    st.set_page_config(
        page_title="OmniMedia - Universal Social Media Media Extractor",
        page_icon="📥",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    tracker = get_history_tracker()
    config = get_config()

    # --- Sidebar: Diagnostics & Settings ---
    with st.sidebar:
        st.header("⚙️ System Status")
        ffmpeg_bin = find_ffmpeg()
        if ffmpeg_bin:
            st.success("FFmpeg: Ready")
            st.caption(f"Path: `{ffmpeg_bin}`")
        else:
            st.warning("FFmpeg: Not detected (some video/audio merges may be limited)")

        st.markdown("---")
        st.subheader("📁 Default Directory")
        st.code(config.default_output_dir, language="bash")
        if st.button("📂 Open Default Folder in Explorer"):
            open_in_explorer(config.default_output_dir)

        st.markdown("---")
        st.markdown(
            "**Supported Platforms:**\n"
            "- 📸 Instagram (Carousels, Reels, Photos)\n"
            "- 🎵 TikTok (Video, Slides, Audio)\n"
            "- 🎬 YouTube & Shorts (4K, 1080p, MP3)\n"
            "- 🐦 Twitter / X (Photos, Videos, GIFs)\n"
            "- 👽 Reddit (Galleries, v.redd.it)\n"
            "- 📌 Pinterest (Original Pins)\n"
            "- 📘 Facebook (Reels & Videos)\n"
            "- 🌐 1,000+ other websites\n"
        )

    # --- Main Header ---
    st.title("📥 OmniMedia Extractor & Monitor")
    st.markdown("Download high-definition photos, pristine audio (MP3), and videos from any social media link.")

    tab_download, tab_monitor, tab_raw_logs = st.tabs([
        "🚀 Extract Media",
        "📊 History & Monitoring",
        "📜 Live Activity Logs"
    ])

    # =========================================================================
    # TAB 1: EXTRACT MEDIA
    # =========================================================================
    with tab_download:
        col_main, col_opt = st.columns([3, 2])

        with col_main:
            url = st.text_input(
                "🔗 Social Media Post Link",
                placeholder="Paste Instagram, TikTok, YouTube, X, Reddit, or Pinterest post link...",
                help="Accepts any public post, carousel, reel, or video URL."
            )
            output_dir = st.text_input(
                "📁 Destination Save Directory",
                value=config.default_output_dir,
                help="Choose where files should be stored on your computer."
            )

        with col_opt:
            media_filter = st.selectbox(
                "Media Filter",
                options=["All Media (Photos + Videos)", "Photos / Images Only", "Videos Only", "Audio Only (MP3)"],
                index=0
            )
            quality = st.selectbox(
                "Quality Tier",
                options=["Highest Available (Best)", "1080p Full HD", "720p HD"],
                index=0
            )

        col_sub, col_jpg = st.columns(2)
        with col_sub:
            subfolder = st.checkbox("Organize in author subfolder", value=config.create_author_subfolder)
        with col_jpg:
            convert_jpg = st.checkbox("Convert WebP images to JPG", value=config.convert_webp_to_jpg)

        filter_map = {
            "All Media (Photos + Videos)": MediaFilter.ALL,
            "Photos / Images Only": MediaFilter.IMAGES_ONLY,
            "Videos Only": MediaFilter.VIDEOS_ONLY,
            "Audio Only (MP3)": MediaFilter.AUDIO_ONLY,
        }

        quality_map = {
            "Highest Available (Best)": MediaQuality.BEST,
            "1080p Full HD": MediaQuality.HIGH,
            "720p HD": MediaQuality.MEDIUM,
        }

        if st.button("🚀 Extract & Download Media", type="primary", use_container_width=True):
            if not url.strip():
                st.error("Please enter a valid social media URL.")
            else:
                config.create_author_subfolder = subfolder
                config.convert_webp_to_jpg = convert_jpg
                config.default_output_dir = output_dir
                save_config(config)

                os.makedirs(output_dir, exist_ok=True)
                manager = ExtractorManager(config)

                progress_bar = st.progress(10, text="Initializing download engine...")

                def web_progress(step, total, msg):
                    pct = int(step / total * 100) if total > 0 else 50
                    progress_bar.progress(min(pct, 100), text=msg)

                result = manager.extract(
                    url=url.strip(),
                    output_dir=output_dir,
                    media_filter=filter_map[media_filter],
                    quality=quality_map[quality],
                    progress_cb=web_progress,
                )
                progress_bar.progress(100, text="Completed!")

                if result.success and result.downloaded_files:
                    st.success(f"🎉 Successfully extracted {len(result.downloaded_files)} file(s) into: `{result.target_dir}`")

                    btn_col1, btn_col2 = st.columns([1, 4])
                    with btn_col1:
                        if st.button("📂 Open Output Folder"):
                            open_in_explorer(result.target_dir)

                    st.subheader("Downloaded Files:")
                    for fp in result.downloaded_files:
                        sz = format_bytes(os.path.getsize(fp)) if os.path.exists(fp) else ""
                        st.markdown(f"- 📄 **`{os.path.basename(fp)}`** ({sz})")

                    if result.metadata_file and os.path.exists(result.metadata_file):
                        with st.expander("📄 View Extracted Metadata (JSON)"):
                            with open(result.metadata_file, "r", encoding="utf-8") as mf:
                                st.code(mf.read(), language="json")

                elif result.success and not result.downloaded_files:
                    st.warning("Extraction completed, but no media matched your selected filter.")
                else:
                    st.error(f"❌ Extraction Failed: {result.error_message}")

    # =========================================================================
    # TAB 2: HISTORY & MONITORING
    # =========================================================================
    with tab_monitor:
        st.subheader("📊 Extraction Monitoring Dashboard")

        stats = tracker.get_stats()
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("Total Runs", stats["total_runs"])
        kpi2.metric("Successes", stats["success_count"], delta=f"{stats['success_rate_percent']}% rate")
        kpi3.metric("Failures", stats["failed_count"], delta_color="inverse")
        kpi4.metric("Total Files", stats["total_files_downloaded"])
        kpi5.metric("Total Data Size", format_bytes(stats["total_bytes_downloaded"]))

        st.markdown("---")

        records = tracker.get_all()
        if not records:
            st.info("No extraction history recorded yet. Run a download from the 'Extract Media' tab!")
        else:
            col_filter, col_search, col_action = st.columns([2, 3, 2])
            with col_filter:
                status_choice = st.selectbox("Filter by Status", ["All", "SUCCESS", "FAILED", "EMPTY"])
            with col_search:
                search_query = st.text_input("🔍 Search URL / Platform", "")
            with col_action:
                st.write("")
                if st.button("🗑️ Clear History"):
                    tracker.clear()
                    st.rerun()

            filtered = records
            if status_choice != "All":
                filtered = [r for r in filtered if r.get("status") == status_choice]
            if search_query.strip():
                q = search_query.strip().lower()
                filtered = [r for r in filtered if q in r.get("url", "").lower() or q in r.get("platform", "").lower()]

            st.write(f"Showing **{len(filtered)}** record(s):")

            for rec in filtered:
                is_success = rec.get("status") == "SUCCESS"
                badge = "🟢 SUCCESS" if is_success else ("🔴 FAILED" if rec.get("status") == "FAILED" else "🟡 EMPTY")

                with st.expander(f"{badge} | {rec.get('timestamp')} | {rec.get('platform')} | {rec.get('total_files')} files ({format_bytes(rec.get('total_bytes', 0))})"):
                    st.markdown(f"**URL:** [{rec.get('url')}]({rec.get('url')})")
                    st.markdown(f"**Platform:** `{rec.get('platform')}` | **Target Directory:** `{rec.get('target_dir')}`")
                    st.markdown(f"**Filter:** `{rec.get('filter')}` | **Quality:** `{rec.get('quality')}` | **Duration:** `{rec.get('duration_seconds')}s`")

                    if rec.get("error_message"):
                        st.error(f"Error Details: {rec.get('error_message')}")

                    if rec.get("files"):
                        st.markdown("**Downloaded Items:**")
                        for f in rec.get("files"):
                            st.write(f"- `{f.get('filename')}` ({format_bytes(f.get('size_bytes'))})")

    # =========================================================================
    # TAB 3: LIVE ACTIVITY LOGS
    # =========================================================================
    with tab_raw_logs:
        st.subheader("📜 Real-Time Audit Log (activity.log)")
        log_path = tracker.log_file

        col_l1, col_l2 = st.columns([4, 1])
        with col_l1:
            st.caption(f"Log Location: `{log_path}`")
        with col_l2:
            if st.button("🔄 Refresh Logs"):
                st.rerun()

        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as lf:
                    lines = lf.readlines()
                    st.text_area(
                        "Live Log Output",
                        value="".join(reversed(lines[-100:])),  # Show last 100 lines reversed
                        height=400
                    )
            except Exception as e:
                st.error(f"Could not read log file: {e}")
        else:
            st.info("No activity log file created yet.")


if __name__ == "__main__":
    run_web_app()
