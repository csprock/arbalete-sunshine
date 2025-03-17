import os
import requests
import pandas as pd
import zipfile
import io
from tqdm import tqdm
import csv

def download_and_extract_gml(url, data_dir, filename=None):
    """
    Download a zip file from URL, extract GML file, and save it to data directory
    
    Args:
        url: URL of the zip file
        data_dir: Directory to save the GML file
        filename: Optional custom filename for the GML file
    
    Returns:
        Path to the extracted GML file or None if failed
    """
    try:
        # Download the zip file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Extract the zip content
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # Find GML files in the archive
            gml_files = [f for f in zip_file.namelist() if f.lower().endswith('.gml')]
            
            if not gml_files:
                print(f"No GML file found in {url}")
                return None
            
            # Extract the first GML file
            gml_content = zip_file.read(gml_files[0])
            
            # Create output filename
            if filename:
                output_file = os.path.join(data_dir, filename)
            else:
                # Use original filename or create one based on URL
                base_name = os.path.basename(gml_files[0])
                if not base_name:
                    base_name = f"file_{hash(url)}.gml"
                output_file = os.path.join(data_dir, base_name)
            
            # Save to disk
            with open(output_file, 'wb') as f:
                f.write(gml_content)
            
            return output_file
    
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return None

def process_csv(csv_path, data_dir):
    """
    Process a CSV file containing URLs in the first column
    
    Args:
        csv_path: Path to the CSV file
        data_dir: Directory to save the extracted GML files
    """
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Read URLs from CSV file
    urls = []
    with open(csv_path, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        # Skip header if exists
        header = next(csv_reader, None)
        
        for row in csv_reader:
            if row and len(row) > 0 and row[0].strip():
                urls.append(row[0].strip())
    
    # Process each URL
    print(f"Processing {len(urls)} URLs...")
    for i, url in enumerate(tqdm(urls)):
        output_file = download_and_extract_gml(url, data_dir)
        if output_file:
            tqdm.write(f"[{i+1}/{len(urls)}] Extracted: {os.path.basename(output_file)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download and extract GML files from URLs in a CSV file")
    parser.add_argument("csv_file", help="Path to the CSV file containing URLs in the first column")
    parser.add_argument("--data_dir", default="data", help="Directory to save the GML files (default: 'data')")
    
    args = parser.parse_args()
    
    process_csv(args.csv_file, args.data_dir)
    print("Processing complete!")