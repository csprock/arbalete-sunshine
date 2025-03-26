#!/bin/bash

# Default values
path_to_files=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --path=*)
      path_to_files="${1#*=}"
      shift
      ;;
    --path)
      path_to_files="$2"
      shift 2
      ;;
    *)
      echo "Unknown parameter: $1"
      echo "Usage: $0 --path=/path/to/gml/files"
      exit 1
      ;;
  esac
done

# Check if path_to_files is provided
if [ -z "$path_to_files" ]; then
  echo "Error: --path parameter is required"
  echo "Usage: $0 --path=/path/to/gml/files"
  exit 1
fi

# Check if the directory exists
if [ ! -d "$path_to_files" ]; then
  echo "Error: Directory '$path_to_files' does not exist"
  exit 1
fi

# Run the conversion
echo "Converting GML files in '$path_to_files' to CityJSON..."
docker run --rm -u 1000 -v "$path_to_files":/data citygml4j/citygml-tools to-cityjson /data/*.gml

echo "Conversion complete!"