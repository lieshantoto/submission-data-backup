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
    'Tribe Name', 'Test Environment', 'Platform', 'Test Case ID', 'Error Summary'
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

# Function to extract a short error summary from the description
def extract_error_summary(desc):
    if not desc:
        return ""
    
    # Convert to lowercase for easier matching
    desc_lower = desc.lower()
    
    # Look for specific WebDriver element errors with selectors
    element_selector_match = re.search(r'element \("([^"]+)"\) still not displayed after \d+ms', desc)
    if element_selector_match:
        selector = element_selector_match.group(1)
        # Extract meaningful part of selector
        if 'sdet-' in selector:
            element_name = selector.replace('~sdet-', '').replace('sdet-', '')
        elif '~' in selector:
            element_name = selector.replace('~', '')
        else:
            element_name = selector[:20]
        return f"Element '{element_name}' not displayed"
    
    # Look for element not clickable/interactable errors
    not_clickable_match = re.search(r'element \("([^"]+)"\).*not clickable', desc_lower)
    if not_clickable_match:
        selector = not_clickable_match.group(1)
        element_name = selector.replace('~sdet-', '').replace('~', '')[:20]
        return f"Element '{element_name}' not clickable"
    
    # Look for "Can't call" errors with method and selector
    cant_call_match = re.search(r"can't call (\w+) on element with selector.*?contains\(@text[^\"]*\"([^\"]+)\"", desc_lower)
    if cant_call_match:
        method = cant_call_match.group(1)
        text_content = cant_call_match.group(2)[:30]
        return f"Can't {method} element with text '{text_content}'"
    
    # Look for generic "Can't call" errors
    cant_call_generic = re.search(r"can't call (\w+) on element", desc_lower)
    if cant_call_generic:
        method = cant_call_generic.group(1)
        return f"Can't {method} element"
    
    # Look for AssertionError with more context
    if 'assertionerror' in desc_lower:
        # Try to find what was being verified
        verify_match = re.search(r'at \w*\.(\w*verify\w*)', desc_lower)
        if verify_match:
            verify_method = verify_match.group(1)
            # Clean up method name
            clean_method = re.sub(r'verify|page|success|trx', '', verify_method).strip()
            if clean_method:
                return f"Assertion failed: {clean_method[:20]}"
        
        # Look for expected vs actual values
        expected_match = re.search(r'expected.*?(\w+).*?actual.*?(\w+)', desc_lower)
        if expected_match:
            expected = expected_match.group(1)
            actual = expected_match.group(2)
            return f"Expected '{expected}' but got '{actual}'"
        
        return "Assertion failed"
    
    # Look for common automation error patterns
    error_patterns = [
        (r'timeout.*waiting.*element', 'Element timeout'),
        (r'element.*not.*found', 'Element not found'),
        (r'no.*such.*element', 'Element not found'),
        (r'stale.*element', 'Stale element'),
        (r'element.*not.*visible', 'Element not visible'),
        (r'connection.*refused', 'Connection refused'),
        (r'network.*error', 'Network error'),
        (r'null.*pointer', 'Null pointer'),
        (r'index.*out.*of.*bounds', 'Index out of bounds'),
        (r'session.*not.*found', 'Session expired'),
        (r'webdriver.*exception', 'WebDriver error'),
        (r'screenshot.*failed', 'Screenshot failed'),
        (r'page.*not.*loaded', 'Page load failed'),
        (r'certificate.*error', 'Certificate error'),
        (r'permission.*denied', 'Permission denied'),
        (r'file.*not.*found', 'File not found'),
        (r'invalid.*selector', 'Invalid selector'),
        (r'function timed out', 'Function timeout'),
        (r'scenario skipped', 'Test skipped'),
    ]
    
    # Check for specific error patterns
    for pattern, summary in error_patterns:
        if re.search(pattern, desc_lower):
            return summary
    
    # Look for exception types
    exception_match = re.search(r'([A-Za-z0-9_]+(?:Exception|Error))', desc)
    if exception_match:
        exception_name = exception_match.group(1)
        # Simplify common exception names
        if 'TimeoutException' in exception_name:
            return 'Timeout error'
        elif 'NoSuchElementException' in exception_name:
            return 'Element not found'
        elif 'ElementNotInteractableException' in exception_name:
            return 'Element not clickable'
        elif 'StaleElementReferenceException' in exception_name:
            return 'Stale element'
        elif 'WebDriverException' in exception_name:
            return 'WebDriver error'
        else:
            return exception_name.replace('Exception', ' error').replace('Error', ' error')
    
    # Look for "failed" keyword with context
    failed_match = re.search(r'failed\s+(?:to\s+)?([a-zA-Z\s]{1,30})', desc_lower)
    if failed_match:
        context = failed_match.group(1).strip()
        return f"Failed to {context[:25]}"
    
    # If no specific pattern found, try to get first meaningful line
    lines = desc.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and len(line) > 10:  # Skip very short lines
            # Take up to 6 words or 60 characters
            words = line.split()[:6]
            summary = ' '.join(words)
            if len(summary) > 60:
                summary = summary[:57] + '...'
            return summary
    
    return "Unknown error"

# Function to extract test case properties from name
def extract_test_properties(name, ntc_id=None):
    if not name:
        return [""] * 9  # Return empty strings for all properties including Error Summary
    
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
        match2 = re.search(r'-\s*([^-()]+)\s*\(', name)
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
    # Parse command line arguments for optional flags
    import argparse
    
    parser = argparse.ArgumentParser(description='Process Notion test case data from CSV files')
    parser.add_argument('input_file', nargs='?', help='Input CSV file path')
    parser.add_argument('--separate-csv', action='store_true', help='Create separate CSV files for each OS')
    parser.add_argument('--separate-txt', action='store_true', help='Create separate TXT files for each OS')
    parser.add_argument('--no-txt', action='store_true', help='Skip TXT file generation completely')
    
    args = parser.parse_args()
    
    if args.input_file:
        input_file = args.input_file
    elif len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        # Legacy support: first non-flag argument is input file
        input_file = sys.argv[1]
    else:
        # Use GUI file dialog
        root = tk.Tk()
        root.withdraw()
        input_file = filedialog.askopenfilename(
            title="Select CSV file to process",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        root.destroy()
        if not input_file:
            print("No file selected.")
            sys.exit(1)
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
                        
                        # Extract error summary from description field (index 5)
                        error_summary = ""
                        if len(incomplete_row) > 4 and len(incomplete_row) > 5 and incomplete_row[5]:
                            status = incomplete_row[4].lower() if incomplete_row[4] else ''
                            if status and status not in ['passed', 'pass', 'success', 'successful']:
                                error_summary = extract_error_summary(incomplete_row[5])
                        incomplete_row.append(error_summary)
                        
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
                    # Extract error summary from description field (index 5) only if status indicates failure
                    error_summary = ""
                    if len(row) > 4 and len(row) > 5 and row[5]:
                        status = row[4].lower() if row[4] else ''
                        if status and status not in ['passed', 'pass', 'success', 'successful']:
                            error_summary = extract_error_summary(row[5])
                    new_row = row + properties + [error_summary]
                    
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
                
                # Extract error summary from description field (index 5) if not already added
                if len(incomplete_row) <= len(headers) + len(NEW_HEADERS) - 1:  # If error summary not added yet
                    error_summary = ""
                    if len(incomplete_row) > 4 and len(incomplete_row) > 5 and incomplete_row[5]:
                        status = incomplete_row[4].lower() if incomplete_row[4] else ''
                        if status and status not in ['passed', 'pass', 'success', 'successful']:
                            error_summary = extract_error_summary(incomplete_row[5])
                    incomplete_row.append(error_summary)
                
                cleaned_rows.append(incomplete_row)
        
        # Write cleaned data to output file
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerows(cleaned_rows)
        
        # Also create a date-stamped version of the output file
        with open(output_file_with_date, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerows(cleaned_rows)
        
        # Create separate CSV files for each OS if requested
        def write_separate_os_csv_files(rows, base_filename, base_filename_dated):
            headers = rows[0]
            data_rows = rows[1:]
            
            # Find OS Name column index
            os_name_idx = None
            for i, header in enumerate(headers):
                if header == 'OS Name':
                    os_name_idx = i
                    break
            
            # Group records by OS Name
            os_groups = {}
            for row in data_rows:
                os_name = row[os_name_idx] if os_name_idx and os_name_idx < len(row) and row[os_name_idx] else 'Unknown_OS'
                if os_name not in os_groups:
                    os_groups[os_name] = []
                os_groups[os_name].append(row)
            
            # Create individual CSV files for each OS
            csv_files_created = []
            for os_name, records in os_groups.items():
                # Create safe filename (replace spaces and special chars)
                safe_os_name = os_name.replace(' ', '_').replace('&', 'and').replace('+', 'Plus')
                
                # Current version
                os_csv_file = base_filename.replace('.csv', f'_OS_{safe_os_name}.csv')
                csv_files_created.append(os_csv_file)
                with open(os_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)  # Write headers
                    writer.writerows(records)  # Write records
                
                # Date-stamped version
                os_csv_file_dated = base_filename_dated.replace('.csv', f'_OS_{safe_os_name}.csv')
                csv_files_created.append(os_csv_file_dated)
                with open(os_csv_file_dated, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)  # Write headers
                    writer.writerows(records)  # Write records
            
            return csv_files_created

        # Function for combined TXT output (original behavior)
        def write_combined_txt_output(filename, rows):
            with open(filename, 'w', encoding='utf-8') as txtfile:
                txtfile.write("=" * 80 + "\n")
                txtfile.write("NOTION TEST CASE DATA PROCESSING SUMMARY\n")
                txtfile.write("=" * 80 + "\n\n")
                txtfile.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                txtfile.write(f"Total Records: {len(rows)-1}\n")
                txtfile.write(f"Source: {input_file}\n\n")
                
                # Skip header row for processing
                headers = rows[0]
                data_rows = rows[1:]
                
                # Find OS Name column index
                os_name_idx = None
                for i, header in enumerate(headers):
                    if header == 'OS Name':
                        os_name_idx = i
                        break
                
                # Group records by OS Name for summary
                os_groups = {}
                for row in data_rows:
                    os_name = row[os_name_idx] if os_name_idx and os_name_idx < len(row) and row[os_name_idx] else 'Unknown OS'
                    if os_name not in os_groups:
                        os_groups[os_name] = []
                    os_groups[os_name].append(row)
                
                # Write summary statistics
                txtfile.write("OS DISTRIBUTION:\n")
                txtfile.write("-" * 40 + "\n")
                for os_name, records in sorted(os_groups.items()):
                    txtfile.write(f"{os_name}: {len(records)} records\n")
                txtfile.write("\n" + "=" * 80 + "\n\n")
                
                # Process each OS group
                for os_name in sorted(os_groups.keys()):
                    records = os_groups[os_name]
                    txtfile.write(f"OS: {os_name}\n")
                    txtfile.write("=" * 60 + "\n")
                    txtfile.write(f"Records: {len(records)}\n\n")
                    
                    for i, row in enumerate(records, 1):
                        txtfile.write(f"Record #{i}\n")
                        txtfile.write("-" * 30 + "\n")
                        
                        # Key information
                        key_fields = [
                            ('ID', 0), ('Name', 1), ('Status', 4), ('App Version', -8), ('Test Case ID', -1), ('Error Summary', -2)
                        ]
                        
                        for field_name, idx in key_fields:
                            if idx < 0:  # Negative indices for extracted fields
                                actual_idx = len(row) + idx
                            else:
                                actual_idx = idx
                            
                            if actual_idx < len(row) and row[actual_idx]:
                                txtfile.write(f"{field_name}: {row[actual_idx]}\n")
                        
                        # Technical details
                        tech_fields = [
                            ('Tribe Short', -7), ('Squad Name', -6), ('Platform', -3), ('Test Environment', -4)
                        ]
                        
                        txtfile.write("\nTechnical Details:\n")
                        for field_name, idx in tech_fields:
                            actual_idx = len(row) + idx if idx < 0 else idx
                            if actual_idx < len(row) and row[actual_idx]:
                                txtfile.write(f"  {field_name}: {row[actual_idx]}\n")
                        
                        # URL if available
                        if len(row) > 2 and row[2]:
                            txtfile.write(f"\nArchive URL: {row[2]}\n")
                        
                        # Description preview (first 200 chars)
                        if len(row) > 5 and row[5]:
                            desc_preview = row[5][:200].replace('\n', ' ').strip()
                            if len(row[5]) > 200:
                                desc_preview += "..."
                            txtfile.write(f"\nDescription: {desc_preview}\n")
                        
                        txtfile.write("\n" + "-" * 60 + "\n\n")
                    
                    txtfile.write("=" * 80 + "\n\n")

        # Define function for separate TXT output files for each OS
        def write_separate_os_txt_files(rows, base_filename):
            # Skip header row for processing
            headers = rows[0]
            data_rows = rows[1:]
            
            # Find OS Name column index
            os_name_idx = None
            for i, header in enumerate(headers):
                if header == 'OS Name':
                    os_name_idx = i
                    break
            
            # Group records by OS Name
            os_groups = {}
            for row in data_rows:
                os_name = row[os_name_idx] if os_name_idx and os_name_idx < len(row) and row[os_name_idx] else 'Unknown_OS'
                if os_name not in os_groups:
                    os_groups[os_name] = []
                os_groups[os_name].append(row)
            
            # Create summary file with OS distribution
            summary_file = base_filename.replace('.csv', '_summary.txt')
            with open(summary_file, 'w', encoding='utf-8') as summary_txtfile:
                summary_txtfile.write("=" * 80 + "\n")
                summary_txtfile.write("NOTION TEST CASE DATA PROCESSING SUMMARY\n")
                summary_txtfile.write("=" * 80 + "\n\n")
                summary_txtfile.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                summary_txtfile.write(f"Total Records: {len(rows)-1}\n")
                summary_txtfile.write(f"Source: {input_file}\n\n")
                
                summary_txtfile.write("OS DISTRIBUTION:\n")
                summary_txtfile.write("-" * 40 + "\n")
                for os_name, records in sorted(os_groups.items()):
                    summary_txtfile.write(f"{os_name}: {len(records)} records\n")
                summary_txtfile.write(f"\nTotal OS Categories: {len(os_groups)}\n")
                summary_txtfile.write(f"Files Generated:\n")
                for os_name in sorted(os_groups.keys()):
                    safe_os_name = os_name.replace(' ', '_').replace('&', 'and').replace('+', 'Plus')
                    filename = base_filename.replace('.csv', f'_OS_{safe_os_name}.txt')
                    summary_txtfile.write(f"  - {filename}\n")
            
            # Create individual files for each OS
            txt_files_created = []
            for os_name, records in os_groups.items():
                # Create safe filename (replace spaces and special chars)
                safe_os_name = os_name.replace(' ', '_').replace('&', 'and').replace('+', 'Plus')
                os_txt_file = base_filename.replace('.csv', f'_OS_{safe_os_name}.txt')
                txt_files_created.append(os_txt_file)
                
                with open(os_txt_file, 'w', encoding='utf-8') as txtfile:
                    txtfile.write("=" * 80 + "\n")
                    txtfile.write(f"NOTION TEST CASE DATA - OS: {os_name}\n")
                    txtfile.write("=" * 80 + "\n\n")
                    txtfile.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    txtfile.write(f"OS: {os_name}\n")
                    txtfile.write(f"Records: {len(records)}\n")
                    txtfile.write(f"Source: {input_file}\n\n")
                    txtfile.write("=" * 80 + "\n\n")
                    
                    for i, row in enumerate(records, 1):
                        txtfile.write(f"Record #{i}\n")
                        txtfile.write("-" * 30 + "\n")
                        
                        # Key information
                        key_fields = [
                            ('ID', 0), ('Name', 1), ('Status', 4), ('App Version', -8), ('Test Case ID', -1), ('Error Summary', -2)
                        ]
                        
                        for field_name, idx in key_fields:
                            if idx < 0:  # Negative indices for extracted fields
                                actual_idx = len(row) + idx
                            else:
                                actual_idx = idx
                            
                            if actual_idx < len(row) and row[actual_idx]:
                                txtfile.write(f"{field_name}: {row[actual_idx]}\n")
                        
                        # Technical details
                        tech_fields = [
                            ('Tribe Short', -7), ('Squad Name', -6), ('Platform', -3), ('Test Environment', -4)
                        ]
                        
                        txtfile.write("\nTechnical Details:\n")
                        for field_name, idx in tech_fields:
                            actual_idx = len(row) + idx if idx < 0 else idx
                            if actual_idx < len(row) and row[actual_idx]:
                                txtfile.write(f"  {field_name}: {row[actual_idx]}\n")
                        
                        # URL if available
                        if len(row) > 2 and row[2]:
                            txtfile.write(f"\nArchive URL: {row[2]}\n")
                        
                        # Description preview (first 200 chars)
                        if len(row) > 5 and row[5]:
                            desc_preview = row[5][:200].replace('\n', ' ').strip()
                            if len(row[5]) > 200:
                                desc_preview += "..."
                            txtfile.write(f"\nDescription: {desc_preview}\n")
                        
                        txtfile.write("\n" + "-" * 60 + "\n\n")
            
            return txt_files_created, summary_file
        
        # Create separate CSV files for each OS if requested
        csv_files_created = []
        if args.separate_csv:
            csv_files_created = write_separate_os_csv_files(cleaned_rows, output_file, output_file_with_date)
        
        # Handle TXT file generation based on flags
        txt_files_created = []
        summary_files = []
        
        if not args.no_txt:
            if args.separate_txt:
                # Generate separate TXT files for each OS
                txt_files, summary_file = write_separate_os_txt_files(cleaned_rows, output_file)
                txt_files_dated, summary_file_dated = write_separate_os_txt_files(cleaned_rows, output_file_with_date)
                txt_files_created = txt_files
                summary_files = [summary_file, summary_file_dated]
            else:
                # Generate single combined TXT file
                txt_output_file = output_file.replace('.csv', '.txt')
                txt_output_file_with_date = output_file_with_date.replace('.csv', '.txt')
                write_combined_txt_output(txt_output_file, cleaned_rows)
                write_combined_txt_output(txt_output_file_with_date, cleaned_rows)
                txt_files_created = [txt_output_file, txt_output_file_with_date]
        
        # Count unique test case IDs for informational purposes
        unique_ids = set()
        for row in cleaned_rows[1:]:  # Skip header row
            if row[0].startswith('HAT-'):
                unique_ids.add(row[0])
        
        print(f"Data cleaned successfully.")
        print(f"Total records: {len(cleaned_rows)-1}, Unique test cases: {len(unique_ids)}")
        print(f"Output saved to {output_file} and {output_file_with_date}")
        
        # Print CSV file details if separate CSV files were created
        if args.separate_csv:
            unique_csv_files = len(csv_files_created) // 2  # Divide by 2 because we create both current and dated versions
            print(f"CSV files created: {unique_csv_files} OS-specific files")
            for csv_file in csv_files_created[:3]:  # Show first 3 files
                if not csv_file.endswith(f"{datetime.now().strftime('%Y%m%d')}.csv"):  # Don't show dated versions in log
                    print(f"  - {csv_file}")
            if unique_csv_files > 3:
                print(f"  ... and {unique_csv_files-3} more OS-specific CSV files")
        
        # Print TXT file details if TXT files were generated
        if not args.no_txt:
            if args.separate_txt:
                print(f"TXT files created: {len(txt_files_created)} OS-specific files + summary")
                print(f"Summary files: {summary_files[0]} and {summary_files[1]}")
                for txt_file in txt_files_created[:3]:  # Show first 3 files
                    print(f"  - {txt_file}")
                if len(txt_files_created) > 3:
                    print(f"  ... and {len(txt_files_created)-3} more OS-specific TXT files")
            else:
                print(f"TXT files created: {txt_files_created[0]} and {txt_files_created[1]}")
        print(f"Original file size: {os.path.getsize(input_file):,} bytes, New file size: {os.path.getsize(output_file):,} bytes")
        print(f"Size change: {((os.path.getsize(output_file)/os.path.getsize(input_file))*100)-100:.2f}%")

    except Exception as e:
        print(f"Error processing the CSV file: {e}")
        sys.exit(1)