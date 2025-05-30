# Test Case Data Processing Tools

This repository contains tools for processing test case data from different sources:

## 🔧 Tools Available

### 1. MD File Processor (Latest)
**Extract and analyze test case data from Markdown files**

A modern web-based tool for processing test case data from Markdown files in the "History Archive Testcases" folder format.

#### Features:
- 🌐 **Modern Web Interface**: Clean, responsive UI inspired by Streamlit
- 📁 **Folder Selection**: Easy drag-and-drop or browse folder selection
- ⚙️ **Flexible Options**: 
  - Create separate CSV files for each OS
  - Generate separate TXT files for each OS  
  - Skip TXT generation entirely
- 📊 **Real-time Processing**: See progress and results immediately
- 📋 **Multiple Output Formats**: CSV and TXT with detailed summaries

#### Quick Start:
```bash
# Easy launcher (recommended)
python3 launch_web_ui.py

# OR run directly
python3 extract_md_history.py --web

# OR run the standalone web UI
python3 md_streamlit_ui.py
```

#### Command Line Usage:
```bash
# Process MD files from a folder
python3 extract_md_history.py "path/to/md/folder"

# With options
python3 extract_md_history.py "path/to/md/folder" --separate-csv --separate-txt

# Skip TXT files
python3 extract_md_history.py "path/to/md/folder" --no-txt
```

### 2. Notion Data Cleaner
**Clean and process test case data exported from Notion databases**

This tool provides two different approaches for cleaning test case data exported from Notion databases:

#### 2a. Normalized Data Approach (`clean_notion_data.py`)

This script normalizes the test data by:

1. Removing long error stack traces
2. Extracting essential device information (Device, OS, App, Phone Number)
3. Keeping only the latest run for each test case ID
4. Extracting URL-only from Archive Testcase column
5. Extracting test case metadata into separate properties
6. Reducing file size significantly (approximately 60% size reduction)

#### 2b. Historical Data Preservation Approach (`preserve_history.py`)

This script preserves all historical test runs while still cleaning the data:

1. Maintains all historical test run data for each test case
2. Preserves error messages, stack traces, and device information
3. Extracts URL-only from Archive Testcase column 
4. Extracts test case metadata into separate properties
5. Only cleans up formatting issues without removing content
6. Keeps file size similar to the original

## 🚀 Usage Guide

### Option 1: MD File Processor Web Interface (Recommended for MD files)

1. **Launch the web interface:**
   ```bash
   python3 launch_web_ui.py
   ```

2. **Use the web interface:**
   - Click "Browse" to select your folder containing MD files
   - Choose processing options (separate files, output formats)
   - Click "Process Files" and wait for completion
   - View generated files and detailed output

### Option 2: Notion Data Cleaner Web Interface (For Notion CSV exports)

1. **Run the web UI script:**
   ```bash
   python3 web_ui_cleaner.py
   ```

2. **Process your data:**
   - Select your Notion CSV export file
   - Choose between "Preserve Historical Data" or "Normalize Data" options
   - Process the file and view results immediately
   - Download the processed files

## Usage

There are four ways to use these scripts/interfaces:

### Option 3: Traditional Notion Data Cleaner Interfaces

#### 3a. Web-Based Interface (Notion CSV files)

1. Run the web UI script:
   ```
   python3 web_ui_cleaner.py
   ```
   The server will automatically find an available port if the default port 8000 is in use.

2. This will open a web browser with a user-friendly interface where you can:
   - Select your Notion CSV export file
   - Choose between "Preserve Historical Data" or "Normalize Data" options
   - Process the file and see results immediately
   - View detailed statistics about the processed data
   - Automatically download the processed files with just one click
   - Files are available in both regular and date-stamped versions

#### 3b. Graphical User Interface (GUI)

1. Run the UI script:
   ```
   python3 notion_data_cleaner_ui.py
   ```

2. Use the interface to:
   - Click "Browse" to select your Notion CSV export file
   - Choose between "Preserve Historical Data" or "Normalize Data" options
   - Click "Process File" to clean and transform the data
   - View processing results in the status window

### 3. Using Command Line

1. Export your test case data from Notion as CSV
2. Place the CSV file in the same directory as the scripts
3. Update the `input_file` variable in either script to match your CSV filename
4. Run the appropriate script based on your needs:
   ```
   # For normalized data (one record per test case)
   python3 clean_notion_data.py
   
   # For historical data preservation (all test runs)
   python3 preserve_history.py
   ```

5. The scripts will generate output files:
   - For normalized data: `cleaned_data_for_notion_import.csv` and `cleaned_data_for_notion_import_YYYYMMDD.csv`
   - For historical data: `historical_data_for_notion_import.csv` and `historical_data_for_notion_import_YYYYMMDD.csv`

### 4. Processing Markdown Folder

1. Run the UI and select the "Process Markdown Folder" option.
2. Click "Browse" and choose the top-level folder containing your `.md` history logs.
3. Click "Process File" to extract every log entry as individual rows.
4. Two CSVs will be generated:
   - `md_history_for_notion_import.csv` (regular)
   - `md_history_for_notion_import_YYYYMMDD.csv` (timestamped)

These CSVs have the same columns as the historical data script plus file and log metadata.

## What These Scripts Do

### Normalized Data Script

- Preserves all test case IDs
- Keeps only the most recent test results for each test case
- Extracts and preserves device information
- Removes lengthy error traces and Jenkins build information
- Cleans and formats the description field
- Extracts URL from Archive Testcase field
- Parses test case names into separate metadata properties:
  - App Version (e.g., 2.81.0)
  - Tribe Short (e.g., FS)
  - Squad Name (e.g., Wealth)
  - OS Name (e.g., DANA+ & Reksadana)
  - Tribe Name (e.g., Financial Service)
  - Test Environment (e.g., SIT)
  - Platform (e.g., Android/iOS)
  - Test Case ID (e.g., NTC-44378)

### Historical Data Script

- Maintains all test runs for each test case ID
- Preserves all error traces and device information
- Cleans up formatting only (multiple newlines, etc.)
- Ensures error traces are properly formatted
- Maintains the full context of each test run
- Extracts URL from Archive Testcase field
- Parses test case names into separate metadata properties:
  - App Version (e.g., 2.81.0)
  - Tribe Short (e.g., FS)
  - Squad Name (e.g., Wealth)
  - OS Name (e.g., DANA+ & Reksadana)
  - Tribe Name (e.g., Financial Service)
  - Test Environment (e.g., SIT)
  - Platform (e.g., Android/iOS)
  - Test Case ID (e.g., NTC-44378)

After running either script, you can import the cleaned CSV back into your Notion database.

## Requirements

- Python 3.8 or higher (recommended: Python 3.10+)
- Required Python packages:
  - `python-dateutil` (for date normalization)
  - `tkinter` (for GUI, included in most standard Python distributions)
  - Standard libraries: `http.server`, `webbrowser`, `csv`, `os`, `re`, `datetime`, `shutil`, `sys`, `glob`, `json`, `io`
- To install the only required external package, run:
  ```bash
  pip install python-dateutil
  ```
- No other external dependencies required

---

## Customization

You can modify either script to handle additional fields or adjust the cleaning behavior based on your specific needs.

## Created

May 23, 2025
