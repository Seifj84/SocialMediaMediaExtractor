import os
import re
import json
import time
import requests
import io
from PIL import Image

def extract_shortcode(url: str) -> str:
    """Extract shortcode from Instagram post / reel / tv URL."""
    patterns = [
        r'instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)',
        r'/p/([A-Za-z0-9_-]+)',
        r'/reel/([A-Za-z0-9_-]+)'
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise ValueError(f"Could not extract Instagram shortcode from URL: {url}")

def scrape_instagram_post(post_url: str, output_base_dir: str = "."):
    """
    Exports all high-quality images from an Instagram post into a folder
    named after the profile username.
    """
    shortcode = extract_shortcode(post_url)
    print(f"[*] Processing Instagram shortcode: {shortcode}")

    embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }

    session = requests.Session()
    session.headers.update(headers)

    print(f"[*] Fetching post metadata from embed endpoint...")
    resp = session.get(embed_url, timeout=20)
    resp.raise_for_status()

    # Search for contextJSON containing GraphQL data
    m = re.search(r'"contextJSON"\s*:\s*"({.+?})"\s*[,}\]]', resp.text)
    if not m:
        raise RuntimeError("Could not find contextJSON in the embed response.")

    clean_json_str = json.loads(f'"{m.group(1)}"')
    data = json.loads(clean_json_str)

    gql = data.get("gql_data", {}).get("shortcode_media", {})
    if not gql:
        raise RuntimeError("Missing shortcode_media in parsed GraphQL data.")

    owner = gql.get("owner", {})
    username = owner.get("username") or "unknown_user"
    full_name = owner.get("full_name") or ""
    caption_edges = gql.get("edge_media_to_caption", {}).get("edges", [])
    caption = caption_edges[0]["node"]["text"] if caption_edges else ""

    print(f"[+] Profile username: @{username}")
    if full_name:
        print(f"[+] Full name: {full_name}")

    # Create destination folder named after profile name
    target_dir = os.path.join(output_base_dir, username)
    os.makedirs(target_dir, exist_ok=True)
    abs_target_dir = os.path.abspath(target_dir)
    print(f"[+] Output directory: {abs_target_dir}")

    # Collect carousel items or single media item
    items = []
    edges = gql.get("edge_sidecar_to_children", {}).get("edges", [])
    if edges:
        for edge in edges:
            items.append(edge["node"])
    else:
        items.append(gql)

    print(f"[+] Found {len(items)} media item(s). Starting high-quality download...")

    exported = []
    for idx, node in enumerate(items, start=1):
        resources = node.get("display_resources", [])
        if resources:
            best_res = max(resources, key=lambda r: r.get('config_width', 0) * r.get('config_height', 0))
            best_url = best_res.get("src")
            width = best_res.get("config_width")
            height = best_res.get("config_height")
        else:
            best_url = node.get("display_url")
            dim = node.get("dimensions", {})
            width = dim.get("width")
            height = dim.get("height")

        best_url = best_url.replace(r"\/", "/")

        print(f"[*] Downloading [{idx:02d}/{len(items):02d}] {width}x{height}...")
        img_resp = session.get(best_url, timeout=30)
        img_resp.raise_for_status()

        # Save pristine original file to dedicated webp subfolder
        webp_dir = os.path.join(target_dir, "webp")
        os.makedirs(webp_dir, exist_ok=True)
        webp_name = f"{username}_{idx:02d}.webp"
        webp_path = os.path.join(webp_dir, webp_name)
        with open(webp_path, "wb") as f:
            f.write(img_resp.content)

        # Save high-quality JPG version in profile root folder
        jpg_name = f"{username}_{idx:02d}.jpg"
        jpg_path = os.path.join(target_dir, jpg_name)
        try:
            with Image.open(io.BytesIO(img_resp.content)) as im:
                rgb_im = im.convert("RGB")
                rgb_im.save(jpg_path, "JPEG", quality=95, subsampling=0)
        except Exception as e:
            print(f"    [!] Warning converting to JPG: {e}")
            jpg_name = None

        file_size_kb = os.path.getsize(webp_path) / 1024
        print(f"    [OK] Saved {jpg_name} (root) and webp/{webp_name} ({file_size_kb:.1f} KB)")

        exported.append({
            "index": idx,
            "id": node.get("id"),
            "width": width,
            "height": height,
            "webp_file": f"webp/{webp_name}",
            "jpg_file": jpg_name,
            "file_size_kb": round(file_size_kb, 1),
            "media_url": best_url
        })
        time.sleep(0.3)

    # Save detailed metadata
    metadata = {
        "source_url": post_url,
        "shortcode": shortcode,
        "profile": {
            "username": username,
            "full_name": full_name,
            "id": owner.get("id")
        },
        "caption": caption,
        "total_images": len(items),
        "exported_images": exported
    }
    meta_path = os.path.join(target_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[+] Metadata written to: {meta_path}")
    print(f"[SUCCESS] All {len(items)} high-quality images exported to: {abs_target_dir}")
    return abs_target_dir, metadata

if __name__ == "__main__":
    import sys
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.instagram.com/p/DdoWS1KCGwA/?utm_source=ig_web_copy_link&stkn=MzRlODBiNWFlZA=="
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
    scrape_instagram_post(target_url, output_base_dir=output_dir)
