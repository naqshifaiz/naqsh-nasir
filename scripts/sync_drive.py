#!/usr/bin/env python3
"""Sync images from a public Google Drive folder into the repo.

Downloads every image in the folder, generates web-optimized thumbnails,
and writes images/manifest.json (which the gallery reads).

Requires two environment variables:
  DRIVE_FOLDER_ID  – the id of the (publicly shared) Drive folder
  DRIVE_API_KEY    – a Google Cloud API key with the Drive API enabled

Only files in a folder shared as "Anyone with the link" are accessible with
an API key, so nothing private is ever exposed.
"""

import io
import json
import os
import sys
import urllib.parse
import urllib.request

from PIL import Image, ImageOps

API = "https://www.googleapis.com/drive/v3/files"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(ROOT, "images")
FULL_DIR = os.path.join(IMAGES_DIR, "full")
THUMB_DIR = os.path.join(IMAGES_DIR, "thumb")
MANIFEST = os.path.join(IMAGES_DIR, "manifest.json")

THUMB_MAX = 1000       # longest edge of grid thumbnail, px
FULL_MAX = 2200        # longest edge of full (lightbox) image, px
JPEG_QUALITY = 82

EXT_BY_MIME = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


def die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def list_drive_images(folder_id, api_key):
    """Return a list of image file records from the Drive folder."""
    files = []
    page_token = None
    q = "'%s' in parents and mimeType contains 'image/' and trashed = false" % folder_id
    while True:
        params = {
            "q": q,
            "key": api_key,
            "fields": "nextPageToken, files(id, name, mimeType, createdTime, modifiedTime)",
            "pageSize": "1000",
            "orderBy": "createdTime desc",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        if page_token:
            params["pageToken"] = page_token
        url = API + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        files.extend(data.get("files", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return files


def download(file_id, api_key):
    params = {"alt": "media", "key": api_key, "supportsAllDrives": "true"}
    url = API + "/" + file_id + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=180) as resp:
        return resp.read()


def save_resized(img, path, max_edge):
    im = img.copy()
    im.thumbnail((max_edge, max_edge), Image.LANCZOS)
    if path.endswith(".jpg") or path.endswith(".jpeg"):
        im = im.convert("RGB")
        im.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    elif path.endswith(".png"):
        im.save(path, "PNG", optimize=True)
    elif path.endswith(".webp"):
        im.save(path, "WEBP", quality=JPEG_QUALITY)
    else:
        im.save(path)
    return im.size


def main():
    folder_id = os.environ.get("DRIVE_FOLDER_ID", "").strip()
    api_key = os.environ.get("DRIVE_API_KEY", "").strip()
    if not folder_id:
        die("DRIVE_FOLDER_ID is not set.")
    if not api_key:
        die("DRIVE_API_KEY is not set.")

    os.makedirs(FULL_DIR, exist_ok=True)
    os.makedirs(THUMB_DIR, exist_ok=True)

    remote = list_drive_images(folder_id, api_key)
    print("Found %d image(s) in Drive folder." % len(remote))

    manifest_images = []
    keep_full = set()
    keep_thumb = set()

    for rec in remote:
        fid = rec["id"]
        mime = rec.get("mimeType", "")
        ext = EXT_BY_MIME.get(mime, "jpg")
        # Thumbnails are always JPEG (except png/webp keep their type for transparency).
        thumb_ext = "jpg" if ext in ("jpg", "gif") else ext
        full_name = "%s.%s" % (fid, ext)
        thumb_name = "%s.%s" % (fid, thumb_ext)
        full_path = os.path.join(FULL_DIR, full_name)
        thumb_path = os.path.join(THUMB_DIR, thumb_name)

        title = os.path.splitext(rec.get("name", ""))[0]
        title = title.replace("_", " ").replace("-", " ").strip()

        keep_full.add(full_name)
        keep_thumb.add(thumb_name)

        # Skip re-download if we already have both derived files.
        if os.path.exists(full_path) and os.path.exists(thumb_path):
            try:
                with Image.open(full_path) as im:
                    w, h = im.size
            except Exception:
                w, h = (0, 0)
            manifest_images.append({
                "id": fid, "name": title,
                "file": "images/full/" + full_name,
                "thumb": "images/thumb/" + thumb_name,
                "w": w, "h": h,
            })
            continue

        print("Downloading %s (%s)…" % (rec.get("name"), fid))
        try:
            raw = download(fid, api_key)
            img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw)))
        except Exception as e:  # noqa: BLE001
            print("  skipped (%s)" % e, file=sys.stderr)
            continue

        w, h = save_resized(img, full_path, FULL_MAX)
        save_resized(img, thumb_path, THUMB_MAX)
        manifest_images.append({
            "id": fid, "name": title,
            "file": "images/full/" + full_name,
            "thumb": "images/thumb/" + thumb_name,
            "w": w, "h": h,
        })

    # Remove local files that are no longer in the Drive folder.
    for d, keep in ((FULL_DIR, keep_full), (THUMB_DIR, keep_thumb)):
        for fn in os.listdir(d):
            if fn not in keep:
                os.remove(os.path.join(d, fn))
                print("Removed stale %s" % fn)

    manifest = {"count": len(manifest_images), "images": manifest_images}
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print("Wrote manifest with %d image(s)." % len(manifest_images))


if __name__ == "__main__":
    main()
