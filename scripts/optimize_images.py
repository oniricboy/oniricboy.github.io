#!/usr/bin/env python3
"""
Optimize the site's images for the web.

1. Every PNG/JPG that is large (over MIN_BYTES or wider/taller than MAX_SIDE)
   is resized to fit MAX_SIDE and saved as WebP next to the original.
   The original is then removed from the site (it stays in git history).
2. Every reference in the site's HTML/CSS/JS to a PNG/JPG that no longer
   exists, but has a WebP twin, is rewritten to point to the WebP.

Step 2 also fixes pages edited *after* an image was already converted,
so you can keep uploading PNG/JPG and writing ".png" in your pages.

Usage:  python3 scripts/optimize_images.py [repo_root]
"""
import os
import re
import sys

from PIL import Image, ImageOps

MAX_SIDE = 2400          # longest side, in pixels
QUALITY = 85             # WebP quality (0-100)
MIN_BYTES = 200 * 1024   # smaller files that already fit are left alone

# Folders or files that must never be touched
SKIP = (
    "cards/",            # card game, still under construction
    "img/favicon.png",   # used by browsers, manifest and link previews
    "img/logo.png",
    ".git/",
    ".github/",
    "scripts/",
    "node_modules/",
)

IMAGE_EXT = (".png", ".jpg", ".jpeg")
TEXT_EXT = (".html", ".css", ".js", ".webmanifest")


def skipped(rel):
    return any(rel == s or rel.startswith(s) for s in SKIP)


def walk(root, exts):
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in files:
            if name.lower().endswith(exts):
                full = os.path.join(dirpath, name)
                yield os.path.relpath(full, root).replace(os.sep, "/")


def convert(root):
    converted = []
    for rel in sorted(walk(root, IMAGE_EXT)):
        if skipped(rel):
            continue
        src = os.path.join(root, rel)
        size = os.path.getsize(src)
        with Image.open(src) as im:
            if size < MIN_BYTES and max(im.size) <= MAX_SIDE:
                continue
            im = ImageOps.exif_transpose(im)
            icc = im.info.get("icc_profile")
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA" if "A" in im.getbands() or "transparency" in im.info else "RGB")
            # Drop an alpha channel that is fully opaque (smaller file)
            if im.mode == "RGBA" and im.getchannel("A").getextrema()[0] == 255:
                im = im.convert("RGB")
            im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
            dst = os.path.splitext(src)[0] + ".webp"
            opts = {"quality": QUALITY, "method": 6}
            if icc:
                opts["icc_profile"] = icc
            im.save(dst, "WEBP", **opts)
        new = os.path.getsize(dst)
        if new > size * 0.9:
            # WebP didn't help (rare: flat, few-color art). Keep the original.
            os.remove(dst)
            print(f"  {rel}: kept as is (WebP would be {new / 1e6:.2f} MB)")
            continue
        os.remove(src)
        converted.append(rel)
        print(f"  {rel}: {size / 1e6:.1f} MB -> {new / 1e6:.2f} MB")
    return converted


# src="...", href="...", url(...), and quoted strings in JS
REF = re.compile(r"""(["'(])([^"'()\s]+?\.(?:png|jpe?g))(?=[?#"')])""", re.I)


def fix_references(root):
    changed = []
    for rel in sorted(walk(root, TEXT_EXT)):
        if skipped(rel):
            continue
        path = os.path.join(root, rel)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        base = os.path.dirname(rel)

        def repl(m):
            ref = m.group(2)
            if re.match(r"^[a-z]+:|^//", ref, re.I):
                return m.group(0)  # external URL
            target = ref.lstrip("/") if ref.startswith("/") else os.path.normpath(os.path.join(base, ref))
            target = target.replace(os.sep, "/")
            if os.path.exists(os.path.join(root, target)):
                return m.group(0)
            twin = os.path.splitext(target)[0] + ".webp"
            if not os.path.exists(os.path.join(root, twin)):
                return m.group(0)
            return m.group(1) + os.path.splitext(ref)[0] + ".webp"

        new = REF.sub(repl, text)
        if new != text:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
            changed.append(rel)
    return changed


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    print("Converting images:")
    imgs = convert(root)
    if not imgs:
        print("  nothing to convert")
    pages = fix_references(root)
    print("Updated references in:", ", ".join(pages) if pages else "none")


if __name__ == "__main__":
    main()
