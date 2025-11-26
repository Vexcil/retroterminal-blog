import os
import json

# Where your tab files live inside the repo
TABS_DIR = "assets/tabs"
# Where to write the index
OUTPUT = "assets/data/tabs.json"

# File types alphaTab can use
VALID_EXT = {".gp", ".gp3", ".gp4", ".gp5", ".gpx", ".musicxml", ".xml", ".capx"}

def make_title_from_filename(fname: str) -> str:
    # Use just the filename, strip extension
    base = os.path.splitext(os.path.basename(fname))[0]
    # Replace underscores with spaces
    base = base.replace("_", " ")
    # Collapse double spaces etc
    base = " ".join(base.split())
    return base

def main():
    entries = []

    for root, dirs, files in os.walk(TABS_DIR):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in VALID_EXT:
                continue

            full_path = os.path.join(root, f)
            # Convert to URL style path
            url_path = "/" + full_path.replace("\\", "/")

            title = make_title_from_filename(f)

            entries.append({
                "title": title,
                "file": url_path
            })

    # Sort A–Z by title
    entries.sort(key=lambda x: x["title"].lower())

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(entries)} entries to {OUTPUT}")

if __name__ == "__main__":
    main()
