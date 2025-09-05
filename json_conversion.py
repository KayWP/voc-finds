import pandas as pd
import json

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