#!/usr/bin/env python3
"""
Text Normalization Script

This script processes all text files in a directory (including subdirectories),
normalizes the text by removing non-alphabet characters (except spaces and newlines),
and modifies the files in place.

Usage:
    python text-norm.py <directory>

Example:
    python text-norm.py ./data
"""

import re
import sys
from pathlib import Path
from typing import Optional

def normalize_text(text: str) -> str:
    """
    Normalize text by removing non-alphabet characters (except spaces and newlines).
    Preserves Vietnamese diacritics and other Unicode letters.
    """
    # Keep letters (including Unicode), spaces, and newlines
    normalized = re.sub(r'[^\p{L}\s]', '', text, flags=re.UNICODE)
    # Replace multiple whitespace with single space
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()

def process_file(file_path: Path) -> None:
    """Process a single file: read, normalize, and overwrite."""
    try:
        # Read the input file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Normalize the content
        normalized_content = normalize_text(content)
        
        # Write the normalized content back to the same file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(normalized_content)
            
        print(f"Processed: {file_path}")
            
    except UnicodeDecodeError:
        print(f"Warning: Could not decode {file_path} as UTF-8. Skipping.")
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")

def process_directory(directory: Path) -> None:
    """Recursively process all text files in the directory."""
    # Counter for processed files
    processed = 0
    
    # Process all text files
    for file_path in directory.glob('**/*'):
        if file_path.is_file() and file_path.suffix.lower() in ('.txt', '.text', ''):
            process_file(file_path)
            processed += 1
    
    return processed

def main() -> None:
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python text-norm.py <directory>")
        sys.exit(1)
    
    directory = Path(sys.argv[1]).resolve()
    
    # Validate directory
    if not directory.exists() or not directory.is_dir():
        print(f"Error: Directory does not exist: {directory}")
        sys.exit(1)
    
    # Confirm before proceeding
    print(f"WARNING: This will modify all text files in: {directory}")
    print("This operation cannot be undone!")
    response = input("Do you want to continue? (y/n): ")
    
    if response.lower() not in ('y', 'yes'):
        print("Operation cancelled.")
        sys.exit(0)
    
    # Process the directory
    print(f"\nProcessing files in: {directory}")
    
    try:
        processed_count = process_directory(directory)
        print(f"\nSuccessfully processed {processed_count} files.")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()