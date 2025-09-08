import os
import json
import pandas as pd
from jinja2 import Environment, FileSystemLoader
import shutil
from collections import defaultdict

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
        
        # Replace NaN with None and convert tags to list
        for k, v in item.items():
            if pd.isna(v):
                item[k] = None
            elif k == 'tags' and v is not None:
                # Convert tags string to list (split by semicolon and strip whitespace)
                item[k] = [tag.strip() for tag in str(v).split(';') if tag.strip()]

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
TAGS_DIR = os.path.join(OUTPUT_DIR, "tags")

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
            tags = metadata.get(filename, {}).get("tags", [])

            inv_number_str = metadata.get(filename, {}).get("inventory_number", "")
            inventory_number = int(inv_number_str) if inv_number_str.isdigit() else None

            scan_str = str(metadata.get(filename, {}).get("scan", ""))
            scan = int(scan_str) if scan_str.isdigit() else None

            image_info = {
                "filename": filename,
                "path": f"images/{filename}",
                "title": metadata.get(filename, {}).get("title", filename.rsplit('.', 1)[0]),
                "description": metadata.get(filename, {}).get("description", ""),
                "tags": tags,
                "archive": metadata.get(filename, {}).get("archive", ""),
                "inventory_number": inventory_number,
                "scan": scan,
                "finder": metadata.get(filename, {}).get("finder", "")
            }
            images.append(image_info)

    images.sort(key=lambda x: x['title'].lower())
    return images

def get_images_by_tag(images):
    """Group images by their tags"""
    tag_images = defaultdict(list)
    all_tags = set()
    
    for image in images:
        for tag in image['tags']:
            tag_images[tag].append(image)
            all_tags.add(tag)
    
    # Sort images within each tag by title
    for tag in tag_images:
        tag_images[tag].sort(key=lambda x: x['title'].lower())
    
    return dict(tag_images), sorted(all_tags)

def create_tag_slug(tag):
    """Convert tag to URL-friendly slug"""
    return tag.lower().replace(' ', '-').replace('_', '-')

# -----------------------------
# Prepare output directories
# -----------------------------
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

if not os.path.exists(TAGS_DIR):
    os.makedirs(TAGS_DIR)

# Copy static folder
shutil.copytree(STATIC_DIR, os.path.join(OUTPUT_DIR, "static"), dirs_exist_ok=True)

# -----------------------------
# Get images and organize by tags
# -----------------------------
images = get_images_with_metadata()
tag_images, all_tags = get_images_by_tag(images)

# -----------------------------
# Render main gallery.html (all images)
# -----------------------------
template = env.get_template("gallery.html")
gallery_html = template.render(images=images, all_tags=all_tags)

with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(gallery_html)

# -----------------------------
# Render tag galleries
# -----------------------------
for tag in all_tags:
    tag_slug = create_tag_slug(tag)
    tag_dir = os.path.join(TAGS_DIR, tag_slug)
    
    if not os.path.exists(tag_dir):
        os.makedirs(tag_dir)
    
    # Render tag gallery page
    tag_gallery_html = template.render(
        images=tag_images[tag], 
        current_tag=tag,
        all_tags=all_tags
    )
    
    with open(os.path.join(tag_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(tag_gallery_html)

# -----------------------------
# Render individual image_view.html pages
# -----------------------------
image_template = env.get_template("image_view.html")

for image in images:
    # use filename without extension for clean URLs
    page_name = image['filename'].rsplit('.', 1)[0] + ".html"
    html_content = image_template.render(image=image, all_tags=all_tags)
    with open(os.path.join(OUTPUT_DIR, page_name), "w", encoding="utf-8") as f:
        f.write(html_content)

print(f"Static site generated in 'build/' folder.")
print(f"Generated {len(all_tags)} tag galleries: {', '.join(all_tags)}")
print(f"Tag gallery files: {', '.join([f'index_{create_tag_slug(tag)}.html' for tag in all_tags])}")