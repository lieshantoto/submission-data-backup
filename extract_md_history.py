#!/usr/bin/env python3
"""
Module to extract test case data from .md files in a folder (History Archive Testcases)
Output: historical_data_from_md_import.csv and a date-stamped version
"""
import os
import re
import csv
import sys
from datetime import datetime
from preserve_history import extract_test_properties, clean_description, extract_error_summary

try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    tk = None
    filedialog = None

# Update headers to include NTC-ID
MD_HEADERS = [
    'ID', 'Name', 'Archive Testcase URL', 'History Date', 'Status',
    'Device', 'OS', 'App', 'Phone Number', 'Location', 'Step', 'Error',
    'Jenkins Build Number', 'Jenkins URL', 'Triggered by', 'Tested by', 'Type Testing',
    'App Version', 'Tribe Short', 'Squad Name', 'OS Name', 'Tribe Name',
    'Test Environment', 'Platform', 'Test Case ID', 'Error Summary', 'Source File', 'Description',
    'Index'
]

def extract_tribe_name_from_archive(archive_val):
    # Example: ... - OS Insurance - Financial Service - Wealth (SIT, Android) ...
    # Want to extract 'Financial Service' (after 'OS ... - ')
    match = re.search(r'- OS [^-]+ - ([^-]+)', archive_val)
    if match:
        return match.group(1).strip()
    # fallback: try to get before last '('
    match2 = re.search(r'- ([^-]+) \(', archive_val)
    if match2:
        return match2.group(1).strip()
    return ''

def normalize_history_date(date_str):
    # Try to parse various date formats and output ISO 8601 (YYYY-MM-DDTHH:MM:SS)
    import dateutil.parser
    try:
        dt = dateutil.parser.parse(date_str, fuzzy=True)
        return dt.strftime('%Y-%m-%dT%H:%M:%S')
    except Exception:
        return date_str

def parse_description_fields(desc):
    # Extract fields from description block
    fields = {
        'Device': '', 'OS': '', 'App': '', 'Phone Number': '',
        'Location': '', 'Step': '', 'Error': '',
        'Jenkins Build Number': '', 'Jenkins URL': '', 'Triggered by': '',
        'Description': ''
    }
    if not desc:
        return fields
    # Device
    m = re.search(r'Device:\s*([^\n]+)', desc)
    if m: fields['Device'] = m.group(1).strip()
    # OS
    m = re.search(r'OS:\s*([^\n]+)', desc)
    if m: fields['OS'] = m.group(1).strip()
    # App
    m = re.search(r'App:\s*([^\n]+)', desc)
    if m: fields['App'] = m.group(1).strip()
    # Phone Number
    m = re.search(r'Phone Number:\s*([^\n]+)', desc)
    if m: fields['Phone Number'] = m.group(1).strip()
    # Location
    m = re.search(r'Location:\s*([^\n]+)', desc)
    if m: fields['Location'] = m.group(1).strip()
    # Step
    m = re.search(r'Step:\s*([^\n]+)', desc)
    if m: fields['Step'] = m.group(1).strip()
    # Error
    m = re.search(r'Error:\s*([\s\S]+?)(?:\n\w|$)', desc)
    if m: fields['Error'] = m.group(1).strip()
    # Jenkins Build Number
    m = re.search(r'Jenkins Build Number:\s*([^\n]+)', desc)
    if m: fields['Jenkins Build Number'] = m.group(1).strip()
    # Jenkins URL
    m = re.search(r'Jenkins URL:\s*([^\n]+)', desc)
    if m: fields['Jenkins URL'] = m.group(1).strip()
    # Triggered by
    m = re.search(r'Triggered by:\s*([^\n]+)', desc)
    if m: fields['Triggered by'] = m.group(1).strip()
    # Remaining description (remove all above fields)
    desc_clean = desc
    for k in fields:
        if k != 'Description' and fields[k]:
            desc_clean = re.sub(rf'{k}:.*', '', desc_clean)
    fields['Description'] = desc_clean.strip()
    return fields

def extract_ntc_id(name):
    m = re.search(r'(NTC-\d+)', name)
    return m.group(1) if m else ''

def parse_md_entry_block(entry, is_main, main_name, main_url, main_id, source_file, header_name=None):
    data = {h: '' for h in MD_HEADERS}
    data['Source File'] = source_file
    archive_val = ''
    header_for_parse = header_name if header_name else ''
    if is_main:
        name_match = re.search(r"^#\s*(.*)", entry, re.MULTILINE)
        if name_match:
            data['Name'] = name_match.group(1).strip()
        archive_match = re.search(r"Archive Testcase:.*?\((https?://[^\s)]+)\)", entry)
        if archive_match:
            data['Archive Testcase URL'] = archive_match.group(1).strip()
            archive_val = archive_match.group(0)
        id_match = re.search(r"^ID:\s*(HAT-\d+)", entry, re.MULTILINE)
        if id_match:
            data['ID'] = id_match.group(1).strip()
    else:
        # For log, try to extract table fields
        # Table row: | Tested By | ... | Status | ... | Testing Type | ... | Description | ... |
        table_match = re.search(r"\|\s*Tested By\s*\|\s*(.*?)\s*\|.*?\|\s*Status\s*\|\s*(.*?)\s*\|.*?\|\s*Testing Type\s*\|\s*(.*?)\s*\|.*?\|\s*Description\s*\|\s*(.*?)\s*\|", entry, re.DOTALL)
        if table_match:
            data['Tested by'] = table_match.group(1).strip()
            data['Status'] = table_match.group(2).strip()
            data['Type Testing'] = table_match.group(3).strip()
            data['Description'] = table_match.group(4).strip()
        # fallback for log name
        data['Name'] = f"{main_name}"
        data['Archive Testcase URL'] = main_url
        data['ID'] = main_id
        archive_val = main_name  # fallback, not used for log
    # For both main and log, fallback for History Date
    if not data['History Date']:
        date_match = re.search(r"^(?:History Date|Log on):\s*(.*)", entry, re.MULTILINE)
        if date_match:
            data['History Date'] = normalize_history_date(date_match.group(1).strip())
    # For both main and log, fallback for Status, Tested by, Type Testing
    if not data['Status']:
        status_match = re.search(r"^(?:Status|\| Status \|):\s*(.*?)(?:\s*\|)?$", entry, re.MULTILINE)
        if status_match:
            data['Status'] = status_match.group(1).strip()
    if not data['Tested by']:
        tested_by_match = re.search(r"^(?:Tested by|\| Tested By \|):\s*(.*?)(?:\s*\|)?$", entry, re.MULTILINE)
        if tested_by_match:
            data['Tested by'] = tested_by_match.group(1).strip()
    if not data['Type Testing']:
        type_testing_match = re.search(r"^(?:Type Testing|\| Testing Type \|):\s*(.*?)(?:\s*\|)?$", entry, re.MULTILINE)
        if type_testing_match:
            data['Type Testing'] = type_testing_match.group(1).strip()
    # Always extract from header/Archive Testcase value
    parse_source = header_for_parse or archive_val or data['Name']
    name_props = extract_test_properties(parse_source)
    for i, h in enumerate(['App Version', 'Tribe Short', 'Squad Name', 'OS Name', 'Tribe Name', 'Test Environment', 'Platform', 'Test Case ID']):
        data[h] = name_props[i]
    
    # Parse description fields
    desc_fields = parse_description_fields(data['Description'])
    for k in desc_fields:
        data[k] = desc_fields[k]
    
    # Extract error summary from Error field or Description only if status indicates failure
    status = data.get('Status', '').lower()
    if status and status not in ['passed', 'pass', 'success', 'successful']:
        error_text = data.get('Error', '') or data.get('Description', '')
        data['Error Summary'] = extract_error_summary(error_text)
    else:
        data['Error Summary'] = ''
    
    data['Description'] = clean_description(data['Description'])
    # Index will be set later
    return [data[h] for h in MD_HEADERS]

def parse_single_md_file(md_file_path):
    rows = []
    source_file = os.path.basename(md_file_path)
    header_name = None
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Get header line (first line, always starts with # Submission ...)
    header_match = re.match(r'^#\s*(.*)', content)
    if header_match:
        header_name = header_match.group(1).strip()
    log_sep = "\n### Log on"
    parts = re.split(f"({log_sep})", content)
    entry_blocks = []
    if not parts:
        return []
    current_block = parts[0]
    for i in range(1, len(parts), 2):
        if i+1 < len(parts):
            entry_blocks.append(current_block)
            current_block = parts[i] + parts[i+1]
        else:
            current_block += parts[i]
    entry_blocks.append(current_block)
    main_name, main_url, main_id = '', '', ''
    main_row = None
    log_rows = []
    if entry_blocks:
        main_row = parse_md_entry_block(entry_blocks[0], True, '', '', '', source_file, header_name)
        main_id = main_row[0]
        main_name = main_row[1] if len(main_row) > 1 else ''
        main_url = main_row[2] if len(main_row) > 2 else ''
        for i in range(1, len(entry_blocks)):
            log_row = parse_md_entry_block(entry_blocks[i], False, main_name, main_url, main_id, source_file, header_name)
            # Ensure log_row always has History Date
            if not log_row[3]:
                date_match = re.search(r"^### Log on (.*)", entry_blocks[i], re.MULTILINE)
                if date_match:
                    log_row[3] = normalize_history_date(date_match.group(1).strip())
            log_rows.append(log_row)
        # Deduplication: if the latest log entry (by History Date) matches the main entry, keep only the log entry
        if log_rows:
            # Sort log_rows by History Date descending
            from dateutil.parser import parse as dtparse
            log_rows_sorted = sorted(log_rows, key=lambda r: dtparse(r[3]), reverse=True)
            latest_log = log_rows_sorted[0]
            # If latest log matches main entry (History Date and Status), only keep logs
            if latest_log[3] == main_row[3] and latest_log[4] == main_row[4]:
                rows.extend(log_rows)
            else:
                rows.append(main_row)
                rows.extend(log_rows)
        else:
            rows.append(main_row)
    return rows

def process_md_folder(folder_path):
    processed_rows = [MD_HEADERS]
    all_rows = []
    for fname in os.listdir(folder_path):
        if fname.lower().endswith('.md'):
            md_file_path = os.path.join(folder_path, fname)
            file_rows = parse_single_md_file(md_file_path)
            all_rows.extend(file_rows)
    # Add index for each test case (Test Case ID + Name): sort by History Date ascending
    from dateutil.parser import parse as dtparse
    def get_key(row):
        # Test Case ID, Name, History Date
        return (row[23], row[1], row[3])
    all_rows.sort(key=get_key)
    last_case = None
    idx = 1
    for row in all_rows:
        case_id = row[23]
        name = row[1]
        if last_case != (case_id, name):
            idx = 1
            last_case = (case_id, name)
        row[-1] = idx
        idx += 1
    processed_rows.extend(all_rows)
    output_file = 'historical_data_from_md_import.csv'
    output_file_with_date = f'historical_data_from_md_import_{datetime.now().strftime("%Y%m%d")}.csv'
    
    # Write CSV files
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(processed_rows)
    with open(output_file_with_date, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(processed_rows)
    
    # Create TXT output files with human-readable format
    txt_output_file = output_file.replace('.csv', '.txt')
    txt_output_file_with_date = output_file_with_date.replace('.csv', '.txt')
    
    def write_txt_output(filename, rows):
        with open(filename, 'w', encoding='utf-8') as txtfile:
            txtfile.write("=" * 80 + "\n")
            txtfile.write("MARKDOWN TEST CASE DATA EXTRACTION SUMMARY\n")
            txtfile.write("=" * 80 + "\n\n")
            txtfile.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            txtfile.write(f"Total Records: {len(rows)-1}\n")
            txtfile.write(f"Source Folder: {folder_path}\n\n")
            
            # Group by Test Case ID for better organization
            headers = rows[0]
            data_rows = rows[1:]
            
            # Group records by Test Case ID
            grouped_records = {}
            for row in data_rows:
                test_case_id = row[23] if len(row) > 23 and row[23] else 'Unknown'
                if test_case_id not in grouped_records:
                    grouped_records[test_case_id] = []
                grouped_records[test_case_id].append(row)
            
            for test_case_id, records in grouped_records.items():
                txtfile.write(f"TEST CASE: {test_case_id}\n")
                txtfile.write("=" * 60 + "\n")
                
                for i, row in enumerate(records, 1):
                    txtfile.write(f"\nExecution #{i}\n")
                    txtfile.write("-" * 30 + "\n")
                    
                    # Key information mapping to MD_HEADERS indices
                    key_fields = [
                        (0, 'ID'), (1, 'Name'), (4, 'Status'), (3, 'History Date'),
                        (17, 'App Version'), (23, 'Test Case ID'), (24, 'Error Summary'),
                        (25, 'Source File')
                    ]
                    
                    for idx, field_name in key_fields:
                        if idx < len(row) and row[idx]:
                            txtfile.write(f"{field_name}: {row[idx]}\n")
                    
                    # Technical details
                    tech_fields = [
                        (18, 'Tribe Short'), (19, 'Squad Name'), (20, 'OS Name'),
                        (22, 'Platform'), (21, 'Test Environment'), (15, 'Tested by'),
                        (16, 'Type Testing')
                    ]
                    
                    txtfile.write("\nTechnical Details:\n")
                    for idx, field_name in tech_fields:
                        if idx < len(row) and row[idx]:
                            txtfile.write(f"  {field_name}: {row[idx]}\n")
                    
                    # Archive URL if available
                    if len(row) > 2 and row[2]:
                        txtfile.write(f"\nArchive URL: {row[2]}\n")
                    
                    # Description preview (first 200 chars)
                    if len(row) > 26 and row[26]:
                        desc_preview = row[26][:200].replace('\n', ' ').strip()
                        if len(row[26]) > 200:
                            desc_preview += "..."
                        txtfile.write(f"\nDescription: {desc_preview}\n")
                    
                    txtfile.write("\n" + "-" * 60 + "\n")
                
                txtfile.write("\n" + "=" * 80 + "\n\n")
    
    write_txt_output(txt_output_file, processed_rows)
    write_txt_output(txt_output_file_with_date, processed_rows)
    
    print(f"MD extraction complete. {len(processed_rows)-1} records written to {output_file} and {output_file_with_date}")
    print(f"TXT output saved to {txt_output_file} and {txt_output_file_with_date}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder = sys.argv[1]
        if not os.path.isdir(folder):
            print("Invalid folder path.")
            sys.exit(1)
        process_md_folder(folder)
    else:
        if tk is None or filedialog is None:
            print("tkinter is required for GUI folder selection.")
            sys.exit(1)
        root = tk.Tk()
        root.withdraw()
        folder = filedialog.askdirectory(title="Select Folder Containing MD Files")
        root.destroy()
        if not folder:
            print("No folder selected.")
            sys.exit(1)
        process_md_folder(folder)
