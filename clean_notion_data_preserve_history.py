#!/usr/bin/env python3

import csv
import re
import sys
import os
from datetime import datetime

# Input and output file paths
input_file = '2.81.0-1fa2556e44dd801c990cf458445e8abe.csv'
output_file = 'cleaned_data_for_notion_import.csv'
output_file_with_date = f'cleaned_data_for_notion_import_{datetime.now().strftime("%Y%m%d")}.csv'

# Check if input file exists
if not os.path.exists(input_file):
    print(f"Error: Input file '{input_file}' not found!")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in current directory: {os.listdir('.')}")
    sys.exit(1)

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

# Read the data and clean it
cleaned_rows = []
incomplete_row = []
in_incomplete_row = False

try:
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        headers = next(reader)  # Read headers
        
        # Add headers to output
        cleaned_rows.append(headers)
        
        for row in reader:
            if not row:  # Skip empty rows
                continue
                
            # Check if this is the start of a new record (starts with HAT-number)
            if row[0] and row[0].strip().startswith('HAT-'):
                # If we were in an incomplete row, add the previously collected incomplete row
                if in_incomplete_row and incomplete_row:
                    cleaned_rows.append(incomplete_row)
                    incomplete_row = []
                
                # Start a new row
                if len(row) < 8:  # If the row is incomplete, pad it
                    row = row + [''] * (8 - len(row))
                
                # Clean description field if it exists
                if len(row) > 5 and row[5]:
                    row[5] = clean_description(row[5])
                    
                # This is a complete row, add directly to cleaned rows
                if len(row) == 8:
                    cleaned_rows.append(row)
                    in_incomplete_row = False
                else:
                    # This is the start of an incomplete row that continues in next lines
                    incomplete_row = row
                    in_incomplete_row = True
            
            # If this is a continuation of a previous record
            elif in_incomplete_row and incomplete_row:
                # Append this content to the description field of the incomplete row
                if len(incomplete_row) > 5:  # If the row has a description field
                    incomplete_row[5] = incomplete_row[5] + "\n" + " ".join(row) if incomplete_row[5] else " ".join(row)
        
        # Don't forget the last incomplete row if there is one
        if in_incomplete_row and incomplete_row:
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
