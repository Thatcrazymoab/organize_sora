from pathlib import Path
import shutil
import csv
import re

SOURCE_DIR = Path("Originals")
OUTPUT_DIR = Path("Organized")

VIDEO_EXTENSIONS = [".mp4", ".mov", ".webm", ".mkv"]


def safe_folder_name(name):
    """Your computer HATES these characters in folder names. Get RID of them"""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


def extract_generation_id(text):
    """Function to try find the generation ID of a video. Muy importante nephew"""
    match = re.search(r"generation id[:\s]+([A-Za-z0-9_-]+)", text, re.IGNORECASE)
    return match.group(1) if match else ""


def extract_prompt(text):
    """Function to try and extract the prompt of a video. Extra muy importante this is where the names are"""
    match = re.search(r"prompt[:\s]+(.+)", text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def find_cameos(prompt):
    """Find all cameo handles in the prompt. The @ symbol tells you its a name."""
    handles = re.findall(r"@[A-Za-z0-9_]+", prompt)
    return sorted(set(handles), key=str.lower)


def handle_to_folder_name(handle):
    """remove @ from the handle for the folder name. Probably unnecessary codingslop but i couldn't tell you if computers hate the @ symbol."""
    return safe_folder_name(handle.lstrip("@"))


def link_or_copy(src, dst):
    """
    Try to create a symlink first.
    If that fails, copy the file instead.
    The cogs are turning twin
    """
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        return

    try:
        dst.symlink_to(src.resolve())
    except Exception:
        shutil.copy2(src, dst)


rows = []

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for txt_file in SOURCE_DIR.glob("*.txt"):
    stem = txt_file.stem

    video_file = None
    for ext in VIDEO_EXTENSIONS:
        candidate = SOURCE_DIR / f"{stem}{ext}"
        if candidate.exists():
            video_file = candidate
            break

    text = txt_file.read_text(encoding="utf-8", errors="ignore")
    generation_id = extract_generation_id(text)
    prompt = extract_prompt(text)
    cameos = find_cameos(prompt)

    if not video_file:
        rows.append({
            "filename": "",
            "txt_file": txt_file.name,
            "generation_id": generation_id,
            "prompt": prompt,
            "cameos": "; ".join(cameos),
            "cameo_count": len(cameos),
            "status": "No matching video found",
        })
        continue

    if not cameos:
        target_folder = OUTPUT_DIR / "By Cameo" / "_No Cameo Detected"
        link_or_copy(video_file, target_folder / video_file.name)
        link_or_copy(txt_file, target_folder / txt_file.name)

    else:
        for cameo in cameos:
            target_folder = OUTPUT_DIR / "By Cameo" / handle_to_folder_name(cameo)
            link_or_copy(video_file, target_folder / video_file.name)
            link_or_copy(txt_file, target_folder / txt_file.name)

        if len(cameos) > 1:
            combo_name = " + ".join(handle_to_folder_name(cameo) for cameo in cameos)
            target_folder = OUTPUT_DIR / "Multi Cameo" / safe_folder_name(combo_name)
            link_or_copy(video_file, target_folder / video_file.name)
            link_or_copy(txt_file, target_folder / txt_file.name)
            """Yes it's in both places the script will make your AI SLOP folder big and rotund and inflated and large."""
    rows.append({
        "filename": video_file.name,
        "txt_file": txt_file.name,
        "generation_id": generation_id,
        "prompt": prompt,
        "cameos": "; ".join(cameos),
        "cameo_count": len(cameos),
        "status": "OK",
    })


index_file = OUTPUT_DIR / "Index" / "sora_index.csv"
index_file.parent.mkdir(parents=True, exist_ok=True)

with index_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "filename",
            "txt_file",
            "generation_id",
            "prompt",
            "cameos",
            "cameo_count",
            "status",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Done. Processed {len(rows)} text files.")
print(f"Index created at: {index_file}")
print(f"UOOOGH ITS SO ORGANIZED NOW SO GOOD")