#!/usr/bin/env python3

import csv
import re
import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

# Define new headers for extracted properties
NEW_HEADERS = [
    'App Version', 'Tribe Short', 'Squad Name', 'OS Name', 
    'Tribe Name', 'Test Environment', 'Platform', 'Test Case ID'
]

# Function to extract URL from Archive Testcase field
def extract_url(archive_testcase):
    if not archive_testcase:
        return ""
    
    # Match the URL pattern inside parentheses
    url_match = re.search(r'\((https?://[^\s)]+)\)', archive_testcase)
    if url_match:
        return url_match.group(1)
    return ""

# Function to extract test case properties from name
def extract_test_properties(name, ntc_id=None):
    if not name:
        return [""] * 8  # Return empty strings for all properties
    
    # Initialize default values
    properties = {
        'App Version': "",
        'Tribe Short': "",
        'Squad Name': "",
        'OS Name': "",
        'Tribe Name': "",
        'Test Environment': "",
        'Platform': "",
        'Test Case ID': ""
    }
    
    # Extract App Version (e.g., 2.81.0)
    app_version_match = re.search(r'(\d+\.\d+\.\d+)', name)
    if app_version_match:
        properties['App Version'] = app_version_match.group(1)
    
    # Extract Tribe Short and Squad Name (e.g., FS Wealth)
    tribe_squad_match = re.search(r'- ([A-Z]+) ([A-Za-z]+) -', name)
    if tribe_squad_match:
        properties['Tribe Short'] = tribe_squad_match.group(1)
        properties['Squad Name'] = tribe_squad_match.group(2)
    
    # Extract OS Name (e.g., DANA CICIL, DANA+ & Reksadana)
    os_name_match = re.search(r'- OS ([^-]+) -', name)
    if os_name_match:
        properties['OS Name'] = os_name_match.group(1).strip()
    
    # Extract Tribe Name (e.g., Financial Service)
    # Use the same logic as extract_tribe_name_from_archive()
    match = re.search(r'- OS [^-]+ - ([^-]+)', name)
    if match:
        properties['Tribe Name'] = match.group(1).strip()
    else:
        # fallback: try to get before last '('
        match2 = re.search(r'-\s*([^-()]+)\s*\(', archive_val)
        if match2:
            properties['Tribe Name'] = match2.group(1).strip()
    
    # Extract Test Environment and Platform (e.g., SIT, Android) - allow multi-word and flexible spacing
    env_platform_match = re.search(r'\(([^,]+),\s*([^)]+)\)', name)
    if env_platform_match:
        properties['Test Environment'] = env_platform_match.group(1).strip()
        properties['Platform'] = env_platform_match.group(2).strip()
    
    # Extract Test Case Tag and Tag ID combined (e.g., NTC-44378)
    # Prefer NTC-ID if provided
    if ntc_id and ntc_id.startswith('NTC-'):
        properties['Test Case ID'] = ntc_id
    else:
        tag_id_match = re.search(r'NTC[ -]+(\d+)', name)
        if tag_id_match:
            properties['Test Case ID'] = f"NTC-{tag_id_match.group(1)}"
        else:
            # fallback to previous pattern
            tag_id_match2 = re.search(r'- ([A-Z]+) - (\d+)', name)
            if tag_id_match2:
                tag = tag_id_match2.group(1)
                id_num = tag_id_match2.group(2)
                properties['Test Case ID'] = f"{tag}-{id_num}"
    
    # Return values in the order defined in NEW_HEADERS
    return [
        properties['App Version'],
        properties['Tribe Short'],
        properties['Squad Name'],
        properties['OS Name'],
        properties['Tribe Name'],
        properties['Test Environment'],
        properties['Platform'],
        properties['Test Case ID']
    ]

# Function to clean description field
def clean_description(desc):
    if not desc:
        return ""
    
    # Just clean up some formatting issues without removing content
    # Replace multiple newlines with a single newline to make it more readable
    clean_desc = re.sub(r'\n{3,}', '\n\n', desc)
    
    # Make sure error traces are properly formatted
    clean_desc = re.sub(r'(\s{4,}at)', '\n    at', clean_desc)
    
    return clean_desc.strip()

# Check if input file exists
if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = None
    if not input_file or not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        sys.exit(1)

    output_file = 'historical_data_for_notion_import.csv'
    output_file_with_date = f'historical_data_for_notion_import_{datetime.now().strftime("%Y%m%d")}.csv'

    # Read the data and clean it
    cleaned_rows = []
    incomplete_row = []
    in_incomplete_row = False

    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            headers = next(reader)  # Read headers
            
            # Create new headers with additional properties
            new_headers = headers + NEW_HEADERS
            
            # Add headers to output
            cleaned_rows.append(new_headers)
            
            for row in reader:
                if not row:  # Skip empty rows
                    continue
                    
                # Check if this is the start of a new record (starts with HAT-number)
                if row[0] and row[0].strip().startswith('HAT-'):
                    # If we were in an incomplete row, add the previously collected incomplete row
                    if in_incomplete_row and incomplete_row:
                        # Extract URL from Archive Testcase field (index 2)
                        if len(incomplete_row) > 2:
                            url = extract_url(incomplete_row[2])
                            incomplete_row[2] = url
                        
                        # Extract properties from the Name field (index 1)
                        if len(incomplete_row) > 1:
                            properties = extract_test_properties(incomplete_row[1])
                            incomplete_row.extend(properties)
                        
                        cleaned_rows.append(incomplete_row)
                        incomplete_row = []
                    
                    # Start a new row
                    if len(row) < 8:  # If the row is incomplete, pad it
                        row = row + [''] * (8 - len(row))
                    
                    # Clean description field if it exists
                    if len(row) > 5 and row[5]:
                        row[5] = clean_description(row[5])
                    
                    # Extract URL from Archive Testcase field (index 2)
                    if len(row) > 2:
                        url = extract_url(row[2])
                        row[2] = url
                    
                    # Extract properties from the Name field (index 1)
                    properties = extract_test_properties(row[1])
                    new_row = row + properties
                    
                    # This is a complete row, add directly to cleaned rows
                    if len(row) == 8:
                        cleaned_rows.append(new_row)
                        in_incomplete_row = False
                    else:
                        # This is the start of an incomplete row that continues in next lines
                        incomplete_row = new_row
                        in_incomplete_row = True
                
                # If this is a continuation of a previous record
                elif in_incomplete_row and incomplete_row:
                    # Append this content to the description field of the incomplete row
                    if len(incomplete_row) > 5:  # If the row has a description field
                        incomplete_row[5] = incomplete_row[5] + "\n" + " ".join(row) if incomplete_row[5] else " ".join(row)
            
            # Don't forget the last incomplete row if there is one
            if in_incomplete_row and incomplete_row:
                # Extract URL from Archive Testcase field (index 2)
                if len(incomplete_row) > 2:
                    url = extract_url(incomplete_row[2])
                    incomplete_row[2] = url
                
                # Extract properties from the Name field (index 1) if not already added
                if len(incomplete_row) <= 8:  # Only extract if properties haven't been added yet
                    properties = extract_test_properties(incomplete_row[1])
                    incomplete_row.extend(properties)
                
                cleaned_rows.append(incomplete_row)
        
        # Write cleaned data to output file
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerows(cleaned_rows)
        
        # Also create a date-stamped version of the output file
        with open(output_file_with_date, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerows(cleaned_rows)
        
        # Count unique test case IDs for informational purposes
        unique_ids = set()
        for row in cleaned_rows[1:]:  # Skip header row
            if row[0].startswith('HAT-'):
                unique_ids.add(row[0])
        
        print(f"Data cleaned successfully.")
        print(f"Total records: {len(cleaned_rows)-1}, Unique test cases: {len(unique_ids)}")
        print(f"Output saved to {output_file} and {output_file_with_date}")
        print(f"Original file size: {os.path.getsize(input_file):,} bytes, New file size: {os.path.getsize(output_file):,} bytes")
        print(f"Size change: {((os.path.getsize(output_file)/os.path.getsize(input_file))*100)-100:.2f}%")

    except Exception as e:
        print(f"Error processing the CSV file: {e}")
        sys.exit(1)