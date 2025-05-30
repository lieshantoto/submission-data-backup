#!/usr/bin/env python3
"""
Module to extract test case data from .md files in a folder (History Archive Testcases)
Output: historical_data_from_md_import.csv and a date-stamped version
"""
import os
import re
import csv
import sys
import argparse
import importlib.util
import dateutil.parser
from datetime import datetime
from preserve_history import extract_test_properties, clean_description, extract_error_summary

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

def process_md_folder(folder_path, args=None):
    # Use default behavior if args is not provided
    if args is None:
        class DefaultArgs:
            separate_csv = False
            separate_txt = False
            no_txt = False
        args = DefaultArgs()
    
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
    
    # Create output directory
    output_dir = 'md_extraction_results'
    os.makedirs(output_dir, exist_ok=True)
    
    # Define output files with directory path
    output_file = os.path.join(output_dir, 'historical_data_from_md_import.csv')
    output_file_with_date = os.path.join(output_dir, f'historical_data_from_md_import_{datetime.now().strftime("%Y%m%d")}.csv')
    
    # Write main CSV files
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(processed_rows)
    with open(output_file_with_date, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(processed_rows)
    
    # Function to create separate CSV files for each OS
    def write_separate_os_csv_files(rows, base_filename, base_filename_dated):
        headers = rows[0]
        data_rows = rows[1:]
        
        # Find OS Name column index (index 20 in MD_HEADERS)
        os_name_idx = 20  # 'OS Name' is at index 20 in MD_HEADERS
        
        # Group records by OS Name
        os_groups = {}
        for row in data_rows:
            os_name = row[os_name_idx] if os_name_idx < len(row) and row[os_name_idx] else 'Unknown_OS'
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
    
    # Write separate OS CSV files if requested
    csv_files_created = []
    if args.separate_csv:
        csv_files_created = write_separate_os_csv_files(processed_rows, output_file, output_file_with_date)
    
    # Create separate TXT output files for each OS
    def write_separate_os_txt_files(rows, base_filename):
        # Group by OS Name instead of Test Case ID
        headers = rows[0]
        data_rows = rows[1:]
        
        # Find OS Name column index (index 20 in MD_HEADERS)
        os_name_idx = 20  # 'OS Name' is at index 20 in MD_HEADERS
        
        # Group records by OS Name
        os_groups = {}
        for row in data_rows:
            os_name = row[os_name_idx] if os_name_idx < len(row) and row[os_name_idx] else 'Unknown_OS'
            if os_name not in os_groups:
                os_groups[os_name] = {}
            
            # Within each OS, group by Test Case ID for sub-organization
            test_case_id = row[23] if len(row) > 23 and row[23] else 'Unknown'
            if test_case_id not in os_groups[os_name]:
                os_groups[os_name][test_case_id] = []
            os_groups[os_name][test_case_id].append(row)
        
        # Create summary file with OS distribution
        summary_file = base_filename.replace('.csv', '_summary.txt')
        with open(summary_file, 'w', encoding='utf-8') as summary_txtfile:
            summary_txtfile.write("=" * 80 + "\n")
            summary_txtfile.write("MARKDOWN TEST CASE DATA EXTRACTION SUMMARY\n")
            summary_txtfile.write("=" * 80 + "\n\n")
            summary_txtfile.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            summary_txtfile.write(f"Total Records: {len(rows)-1}\n")
            summary_txtfile.write(f"Source Folder: {folder_path}\n\n")
            
            summary_txtfile.write("OS DISTRIBUTION:\n")
            summary_txtfile.write("-" * 40 + "\n")
            for os_name, test_cases in sorted(os_groups.items()):
                total_records = sum(len(records) for records in test_cases.values())
                summary_txtfile.write(f"{os_name}: {total_records} records ({len(test_cases)} test cases)\n")
            summary_txtfile.write(f"\nTotal OS Categories: {len(os_groups)}\n")
            summary_txtfile.write(f"Files Generated:\n")
            for os_name in sorted(os_groups.keys()):
                safe_os_name = os_name.replace(' ', '_').replace('&', 'and').replace('+', 'Plus')
                filename = base_filename.replace('.csv', f'_OS_{safe_os_name}.txt')
                summary_txtfile.write(f"  - {filename}\n")
        
        # Create individual files for each OS
        txt_files_created = []
        for os_name, test_cases in os_groups.items():
            # Create safe filename (replace spaces and special chars)
            safe_os_name = os_name.replace(' ', '_').replace('&', 'and').replace('+', 'Plus')
            os_txt_file = base_filename.replace('.csv', f'_OS_{safe_os_name}.txt')
            txt_files_created.append(os_txt_file)
            
            total_records = sum(len(records) for records in test_cases.values())
            
            with open(os_txt_file, 'w', encoding='utf-8') as txtfile:
                txtfile.write("=" * 80 + "\n")
                txtfile.write(f"MARKDOWN TEST CASE DATA - OS: {os_name}\n")
                txtfile.write("=" * 80 + "\n\n")
                txtfile.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                txtfile.write(f"OS: {os_name}\n")
                txtfile.write(f"Test Cases: {len(test_cases)}, Total Records: {total_records}\n")
                txtfile.write(f"Source Folder: {folder_path}\n\n")
                txtfile.write("=" * 80 + "\n\n")
                
                for test_case_id, records in sorted(test_cases.items()):
                    txtfile.write(f"TEST CASE: {test_case_id}\n")
                    txtfile.write("-" * 50 + "\n")
                    
                    for i, row in enumerate(records, 1):
                        txtfile.write(f"Execution #{i}\n")
                        txtfile.write("." * 25 + "\n")
                        
                        # Key information mapping to MD_HEADERS indices
                        key_fields = [
                            (0, 'ID'), (1, 'Name'), (4, 'Status'), (3, 'History Date'),
                            (17, 'App Version'), (24, 'Error Summary'), (25, 'Source File')
                        ]
                        
                        for idx, field_name in key_fields:
                            if idx < len(row) and row[idx]:
                                txtfile.write(f"{field_name}: {row[idx]}\n")
                        
                        # Technical details
                        tech_fields = [
                            (18, 'Tribe Short'), (19, 'Squad Name'), (22, 'Platform'),
                            (21, 'Test Environment'), (15, 'Tested by'), (16, 'Type Testing')
                        ]
                        
                        txtfile.write("\nTechnical Details:\n")
                        for idx, field_name in tech_fields:
                            if idx < len(row) and row[idx]:
                                txtfile.write(f"  {field_name}: {row[idx]}\n")
                        
                        # Archive URL if available
                        if len(row) > 2 and row[2]:
                            txtfile.write(f"\nArchive URL: {row[2]}\n")
                        
                        # Description preview (first 150 chars for better grouping)
                        if len(row) > 26 and row[26]:
                            desc_preview = row[26][:150].replace('\n', ' ').strip()
                            if len(row[26]) > 150:
                                desc_preview += "..."
                            txtfile.write(f"\nDescription: {desc_preview}\n")
                        
                        txtfile.write("\n" + "." * 50 + "\n\n")
                    
                    txtfile.write("-" * 60 + "\n\n")
        
        return txt_files_created, summary_file
    
    # Handle TXT file generation based on flags
    txt_files_created = []
    summary_files = []
    
    if not args.no_txt:
        if args.separate_txt:
            # Generate separate TXT files for each OS
            txt_files, summary_file = write_separate_os_txt_files(processed_rows, output_file)
            txt_files_dated, summary_file_dated = write_separate_os_txt_files(processed_rows, output_file_with_date)
            txt_files_created = txt_files
            summary_files = [summary_file, summary_file_dated]
        else:
            # Generate combined TXT file (if separate_txt is not set)
            def write_combined_txt_output(filename, rows):
                with open(filename, 'w', encoding='utf-8') as txtfile:
                    txtfile.write("=" * 80 + "\n")
                    txtfile.write("MARKDOWN TEST CASE DATA PROCESSING SUMMARY\n")
                    txtfile.write("=" * 80 + "\n\n")
                    txtfile.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    txtfile.write(f"Total Records: {len(rows)-1}\n")
                    txtfile.write(f"Source Folder: {folder_path}\n\n")
                    
                    # Skip header row for processing
                    headers = rows[0]
                    data_rows = rows[1:]
                    
                    # Find OS Name column index (index 20 in MD_HEADERS)
                    os_name_idx = 20  # 'OS Name' is at index 20 in MD_HEADERS
                    
                    # Group records by OS Name for summary
                    os_groups = {}
                    for row in data_rows:
                        os_name = row[os_name_idx] if os_name_idx < len(row) and row[os_name_idx] else 'Unknown OS'
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
                            
                            # Key information mapping to MD_HEADERS indices
                            key_fields = [
                                (0, 'ID'), (1, 'Name'), (4, 'Status'), (3, 'History Date'),
                                (17, 'App Version'), (24, 'Error Summary'), (25, 'Source File')
                            ]
                            
                            for idx, field_name in key_fields:
                                if idx < len(row) and row[idx]:
                                    txtfile.write(f"{field_name}: {row[idx]}\n")
                            
                            # Technical details
                            tech_fields = [
                                (18, 'Tribe Short'), (19, 'Squad Name'), (22, 'Platform'),
                                (21, 'Test Environment'), (15, 'Tested by'), (16, 'Type Testing')
                            ]
                            
                            txtfile.write("\nTechnical Details:\n")
                            for idx, field_name in tech_fields:
                                if idx < len(row) and row[idx]:
                                    txtfile.write(f"  {field_name}: {row[idx]}\n")
                            
                            # Archive URL if available
                            if len(row) > 2 and row[2]:
                                txtfile.write(f"\nArchive URL: {row[2]}\n")
                            
                            # Description preview (first 150 chars for better grouping)
                            if len(row) > 26 and row[26]:
                                desc_preview = row[26][:150].replace('\n', ' ').strip()
                                if len(row[26]) > 150:
                                    desc_preview += "..."
                                txtfile.write(f"\nDescription: {desc_preview}\n")
                            
                            txtfile.write("\n" + "-" * 60 + "\n\n")
                        
                        txtfile.write("=" * 80 + "\n\n")
                return filename

            txt_output_file = output_file.replace('.csv', '.txt')
            txt_output_file_with_date = output_file_with_date.replace('.csv', '.txt')
            write_combined_txt_output(txt_output_file, processed_rows)
            write_combined_txt_output(txt_output_file_with_date, processed_rows)
            txt_files_created = [txt_output_file, txt_output_file_with_date]
            
    # Output report
    print(f"📁 Output directory: {output_dir}")
    print(f"✅ MD extraction complete. {len(processed_rows)-1} records written to:")
    print(f"   📄 {os.path.basename(output_file)}")
    print(f"   📄 {os.path.basename(output_file_with_date)}")
    
    # Print CSV file details if separate CSV files were created
    if args.separate_csv:
        unique_csv_files = len(csv_files_created) // 2  # Divide by 2 because we create both current and dated versions
        print(f"📊 CSV files created: {unique_csv_files} OS-specific files")
        for csv_file in csv_files_created[:3]:  # Show first 3 files
            if not csv_file.endswith(f"{datetime.now().strftime('%Y%m%d')}.csv"):  # Don't show dated versions in log
                print(f"   📄 {os.path.basename(csv_file)}")
        if unique_csv_files > 3:
            print(f"   ... and {unique_csv_files-3} more OS-specific CSV files")
            
    # Print TXT file details if TXT files were generated
    if not args.no_txt:
        if args.separate_txt:
            print(f"📝 TXT files created: {len(txt_files_created)} OS-specific files + summary")
            print(f"📋 Summary files: {os.path.basename(summary_files[0])} and {os.path.basename(summary_files[1])}")
            for txt_file in txt_files_created[:3]:  # Show first 3 files
                print(f"   📄 {os.path.basename(txt_file)}")
            if len(txt_files_created) > 3:
                print(f"   ... and {len(txt_files_created)-3} more OS-specific TXT files")
        else:
            print(f"📝 TXT files created: {os.path.basename(txt_files_created[0])} and {os.path.basename(txt_files_created[1])}")

if __name__ == "__main__":
    # Parse command line arguments for optional flags
    import argparse
    import importlib.util
    
    parser = argparse.ArgumentParser(description='Process MD files into structured data')
    parser.add_argument('folder', nargs='?', help='Folder containing MD files')
    parser.add_argument('--separate-csv', action='store_true', help='Create separate CSV files for each OS')
    parser.add_argument('--separate-txt', action='store_true', help='Create separate TXT files for each OS (default: false)')
    parser.add_argument('--no-txt', action='store_true', help='Skip TXT file generation completely')
    parser.add_argument('--web', action='store_true', help='Use web-based UI for folder selection and options')
    
    args = parser.parse_args()
    
    # Check if web interface is requested
    if args.web or (not args.folder and len(sys.argv) <= 1):
        # Use the primary Streamlit-style UI
        ui_modules = ['md_streamlit_ui']
        
        for ui_module_name in ui_modules:
            web_ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'{ui_module_name}.py')
            if os.path.exists(web_ui_path):
                try:
                    spec = importlib.util.spec_from_file_location(ui_module_name, web_ui_path)
                    web_ui = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(web_ui)
                    
                    # Launch web interface
                    print(f"Starting web interface ({ui_module_name})...")
                    web_ui.start_server()
                    sys.exit(0)
                except Exception as e:
                    print(f"Error starting {ui_module_name}: {e}")
                    continue
        
        print("Error: No web UI module found.")
        print("Please ensure one of the following files exists:")
        for ui_module_name in ui_modules:
            print(f"  - {ui_module_name}.py")
        sys.exit(1)
    
    # Standard command-line mode
    if args.folder:
        folder = args.folder
    elif len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        # Legacy support: first non-flag argument is folder
        folder = sys.argv[1]
    else:
        print("No folder specified. Use --web for web interface or provide folder path.")
        sys.exit(1)
    
    if not os.path.isdir(folder):
        print("Invalid folder path.")
        sys.exit(1)
    
    # Call process_md_folder with the command-line arguments
    process_md_folder(folder, args)
