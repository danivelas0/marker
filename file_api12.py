"""File the API 12 drops into Engineering_Hub/database per its rules 1-6.

For each standard: split the single combined marker JSON into one Document
per top-level Section / Annex (byte-for-byte block content, split at
top-level-heading boundaries, nothing dropped/edited/reordered), write each
as snake_case_source.json with a source block, and pull the already
caption-verified figures out as descriptively-named PNGs.
"""

import base64
import copy
import io
import json
import re
import sys
from pathlib import Path

from PIL import Image

TOPLEVEL = re.compile(r"^(\d{1,2})\s+([A-Z][\w].*)$")
ANNEX = re.compile(r"^Annex\s+([A-Z]+)\b", re.I)
INFORMATIVE_TAG = re.compile(r"^\(\s*(informative|normative)\s*\)$", re.I)


def strip_html(html: str) -> str:
    return re.sub(r"<[^<]+?>", " ", html or "").strip()


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def find_by_id(node, target, cache):
    if not cache:
        def index(n):
            cache[n["id"]] = n
            for c in n.get("children") or []:
                index(c)
        index(node)
    return cache.get(target)


def detect_segments(pages):
    """Return ordered list of dicts: kind, number, title2, page_idx, child_idx."""
    segments = []
    for page in pages:
        pg = int(page["id"].split("/")[2])
        children = page.get("children") or []
        for idx, child in enumerate(children):
            if child.get("block_type") != "SectionHeader" or not child.get("html"):
                continue
            text = strip_html(child["html"])
            m = TOPLEVEL.match(text)
            a = ANNEX.match(text)
            if m:
                segments.append(
                    {"kind": "section", "label": text, "page": pg, "idx": idx, "letter": m.group(1)}
                )
            elif a:
                segments.append(
                    {"kind": "annex", "label": text, "page": pg, "idx": idx, "letter": a.group(1).upper()}
                )
    return segments


def annex_subtitle(pages, seg):
    """The descriptive title printed right after 'Annex X (qualifier)'."""
    for page in pages:
        pg = int(page["id"].split("/")[2])
        if pg != seg["page"]:
            continue
        children = page.get("children") or []
        for idx in range(seg["idx"] + 1, len(children)):
            child = children[idx]
            if child.get("block_type") == "SectionHeader" and child.get("html"):
                text = strip_html(child["html"])
                if INFORMATIVE_TAG.match(text):
                    continue
                return text
        return None
    return None


def slice_pages(pages, start, end):
    """Return a deep-copied list of Page nodes covering [start, end) cut points.

    start/end are (page_idx, child_idx) or None for the very start/end of the
    document. Every block is assigned to exactly one segment: a boundary page
    is split at the heading's child index, no block duplicated or dropped.
    """
    start_page, start_idx = start if start else (None, None)
    end_page, end_idx = end if end else (None, None)

    out = []
    for page in pages:
        pg = int(page["id"].split("/")[2])
        if start_page is not None and pg < start_page:
            continue
        if end_page is not None and pg > end_page:
            continue
        children = page.get("children") or []
        lo = start_idx if (start_page is not None and pg == start_page) else 0
        hi = end_idx if (end_page is not None and pg == end_page) else len(children)
        subset = children[lo:hi]
        if not subset:
            continue
        new_page = copy.deepcopy(page)
        new_page["children"] = copy.deepcopy(subset)
        refs = "".join(f"<content-ref src='{c['id']}'></content-ref>" for c in subset)
        new_page["html"] = refs
        out.append(new_page)
    return out


def collect_images(nodes, out):
    for node in nodes:
        if node.get("images"):
            for key, b64 in node["images"].items():
                out[key] = b64
        collect_images(node.get("children") or [], out)


def build_source(cfg, table, clause, transcribed_from, note_extra=""):
    return {
        "standard": cfg["standard"],
        "edition": cfg["edition"],
        "table": table,
        "clause": clause,
        "transcribed_from": transcribed_from,
        "note": (
            f"Full text of {cfg['standard']} {table} as supplied by Daniel Velasquez on "
            f"2026-08-24 and extracted from the combined standard PDF with marker-pdf "
            f"(--disable_ocr; this machine is CPU-only). `data` is the extractor's output "
            f"verbatim: page blocks with their HTML, text, tables and layout coordinates, "
            f"unedited. This file IS the source document, so `transcribed_from` names its "
            f"own path — it is the artefact under review, not a transcription of one. "
            f"Unlike the API 650/620/625 drops, {cfg['standard']} was supplied as one "
            f"combined PDF (\"{cfg['supplied_as']}\") covering every section and annex, not "
            f"pre-split per clause — so this file is a page-range slice of that single "
            f"extraction rather than an independently-supplied section PDF, and its page "
            f"numbers (e.g. `/page/11/...`) are the combined document's own, not renumbered "
            f"from 0. A heading is the cut point between two files, split at the exact child "
            f"block so nothing is duplicated or dropped across the boundary. Front matter "
            f"(cover, licence/watermark page, Special Notes legal notice, Foreword, Contents) "
            f"and the back-cover ordering-information page are not filed as a section or "
            f"annex because they are not one. {cfg['edition']} is stated on the title page "
            f"itself ({cfg['edition_detail']}). {note_extra}"
        ),
        "status": "PRELIMINARY — supplied source document, transcribed for screening and pre-dimensioning. The published standard governs for issued design.",
        "read_by": "Daniel Velasquez",
        "read_on": "2026-08-24",
    }


def main():
    cfg_path = Path(sys.argv[1])
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    raw = json.loads(Path(cfg["raw_json"]).read_text(encoding="utf-8"))
    all_pages = raw["children"]
    start_page, end_page = cfg["tech_range"]
    pages = [p for p in all_pages if start_page <= int(p["id"].split("/")[2]) <= end_page]

    segments = detect_segments(pages)
    if not segments:
        print("No segments detected!", file=sys.stderr)
        sys.exit(1)

    dest = Path(cfg["dest"])
    sections_dir = dest / "sections"
    annexes_dir = dest / "annexes"
    figures_dir = dest / "figures"
    sections_dir.mkdir(parents=True, exist_ok=True)
    annexes_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    cut_points = [(s["page"], s["idx"]) for s in segments]
    bounds = [None] + cut_points + [None]

    written = []
    for i, seg in enumerate(segments):
        seg_start = cut_points[i]
        seg_end = cut_points[i + 1] if i + 1 < len(cut_points) else None
        sliced = slice_pages(pages, seg_start, seg_end)
        doc = {"block_type": "Document", "children": sliced}

        if seg["kind"] == "section":
            title = re.sub(r"\s+", " ", seg["label"]).strip()
            slug = "section_" + slugify(title)
            table = title.upper() if False else title
            clause = f"Section {seg['letter']}"
            out_path = sections_dir / f"{slug}_source.json"
            extra = ""
        else:
            subtitle = annex_subtitle(pages, seg)
            qualifier_m = re.search(r"\((informative|normative)\)", seg["label"], re.I)
            qualifier = f" ({qualifier_m.group(1).lower()})" if qualifier_m else ""
            title = f"Annex {seg['letter']}{qualifier}" + (f" — {subtitle}" if subtitle else "")
            slug = "annex_" + slugify(seg["letter"]) + (f"_{slugify(subtitle)}" if subtitle else "")
            table = title
            clause = f"Annex {seg['letter']}"
            out_path = annexes_dir / f"{slug}_source.json"
            extra = ""

        transcribed_from = f"database/{cfg['dest'].split('/')[-1]}/{'sections' if seg['kind']=='section' else 'annexes'}/{slug}_source.json"
        extra = cfg.get("clause_notes", {}).get(clause, "")
        source = build_source(cfg, table, clause, transcribed_from, extra)
        out_path.write_text(json.dumps({"source": source, "data": doc}, indent=2), encoding="utf-8")
        written.append((clause, table, out_path, len(sliced)))

    # Figures: reuse the already caption-verified manifest (block_id -> caption).
    manifest = json.loads(Path(cfg["manifest"]).read_text(encoding="utf-8"))
    images = {}
    collect_images(all_pages, images)

    fig_written = []
    for entry in manifest:
        block_id = entry["block_id"]
        caption = entry["caption"]
        b64 = images.get(block_id)
        if not b64:
            print(f"WARNING: no image data for {block_id}", file=sys.stderr)
            continue
        m = re.match(r"^Figure\s+([A-Za-z0-9.]+)\s*—\s*(.+)$", caption)
        if m:
            num_slug = slugify(m.group(1).replace(".", "_"))
            title_slug = slugify(m.group(2))
        else:
            num_slug = "x"
            title_slug = slugify(caption)
        fname = f"figure_{num_slug}_{title_slug}.png"
        img_bytes = base64.b64decode(b64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img.save(figures_dir / fname, "PNG")
        fig_written.append((fname, caption))

    print(f"=== {cfg['standard']} -> {dest} ===")
    for clause, table, path, npages in written:
        print(f"  {clause:14s} {npages:3d} pages  {path}")
    print(f"  {len(fig_written)} figures -> {figures_dir}")
    for fname, caption in fig_written:
        print(f"    {fname}  ({caption})")


if __name__ == "__main__":
    main()
