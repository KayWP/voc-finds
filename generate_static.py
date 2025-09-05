import os
import json
import pandas as pd
from jinja2 import Environment, FileSystemLoader

#------------------------------
# Update Image metadata
#-------------------------------

def convert():
    output_file = "image_metadata.json"
    
    # Read Excel file
    df = pd.read_excel('image_metadata.xlsx')
    data = df.to_dict("records")
    
    # Convert data to JSON-friendly dictionary
    result = {}
    for item in data:
        key = item.pop('image')  # Use 'image' column as key
        # Replace NaN with None
        for k, v in item.items():
            if pd.isna(v):
                item[k] = None
        result[key] = item
    
    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

convert()

# -----------------------------
# Configuration
# -----------------------------
TEMPLATE_DIR = "templates"
OUTPUT_DIR = "build"
STATIC_DIR = "static"
IMAGES_DIR = os.path.join(STATIC_DIR, "images")
METADATA_FILE = "image_metadata.json"

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

# -----------------------------
# Load image metadata
# -----------------------------
def load_image_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {}

def get_images_with_metadata():
    images = []
    metadata = load_image_metadata()

    if not os.path.exists(IMAGES_DIR):
        return images

    for filename in os.listdir(IMAGES_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            image_info = {
                "filename": filename,
                "path": f"images/{filename}",
                "title": metadata.get(filename, {}).get("title", filename.rsplit('.', 1)[0]),
                "description": metadata.get(filename, {}).get("description", ""),
                "tags": metadata.get(filename, {}).get("tags", []),
                "date_taken": metadata.get(filename, {}).get("date_taken", ""),
                "camera": metadata.get(filename, {}).get("camera", ""),
                "location": metadata.get(filename, {}).get("location", "")
            }
            images.append(image_info)

    images.sort(key=lambda x: x['title'].lower())
    return images

# -----------------------------
# Prepare output directories
# -----------------------------
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Copy static folder
import shutil
shutil.copytree(STATIC_DIR, os.path.join(OUTPUT_DIR, "static"), dirs_exist_ok=True)

# -----------------------------
# Render gallery.html
# -----------------------------
images = get_images_with_metadata()
template = env.get_template("gallery.html")
gallery_html = template.render(images=images)

with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(gallery_html)

# -----------------------------
# Render individual image_view.html pages
# -----------------------------
template = env.get_template("image_view.html")

for image in images:
    # use filename without extension for clean URLs
    page_name = image['filename'].rsplit('.', 1)[0] + ".html"
    html_content = template.render(image=image)
    with open(os.path.join(OUTPUT_DIR, page_name), "w", encoding="utf-8") as f:
        f.write(html_content)

print("Static site generated in 'build/' folder.")
