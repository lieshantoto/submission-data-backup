# MD File Processor

A modern tool for processing test case data from Markdown files in the "History Archive Testcases" folder format.

## ✨ Features

- 🌐 **Modern Web Interface**: Clean, responsive UI for easy file processing
- 📁 **Folder Selection**: Drag-and-drop or browse folder selection
- ⚙️ **Flexible Options**: 
  - Create separate CSV files for each OS
  - Generate separate TXT files for each OS  
  - Skip TXT generation entirely
- 📊 **Real-time Processing**: See progress and results immediately
- 📋 **Multiple Output Formats**: CSV and TXT with detailed summaries
- 🔍 **Smart Data Extraction**: Automatically extracts test case metadata, error summaries, and device information

## 🚀 Quick Start

### Web Interface (Recommended)
```bash
# Easy launcher
python3 launch_web_ui.py

# OR run directly with web interface
python3 extract_md_history.py --web

# OR run the standalone web UI
python3 md_streamlit_ui.py
```

### Command Line Usage
```bash
# Process MD files from a folder
python3 extract_md_history.py "path/to/md/folder"

# With options
python3 extract_md_history.py "path/to/md/folder" --separate-csv --separate-txt

# Skip TXT files
python3 extract_md_history.py "path/to/md/folder" --no-txt
```

## 📖 Usage Guide

### Web Interface

1. **Launch the web interface:**
   ```bash
   python3 launch_web_ui.py
   ```

2. **Use the web interface:**
   - Click "Browse" to select your folder containing MD files
   - Choose processing options (separate files, output formats)
   - Click "Process Files" and wait for completion
   - View generated files and detailed output

### Command Line Interface

Process MD files directly from the command line:

```bash
# Basic usage
python3 extract_md_history.py "path/to/md/folder"

# Available options:
--separate-csv    # Create separate CSV files for each OS
--separate-txt    # Create separate TXT files for each OS  
--no-txt         # Skip TXT file generation
--web            # Launch web interface
```

## 📊 What This Tool Does

The MD File Processor extracts and analyzes test case data from Markdown files, specifically designed for "History Archive Testcases" folder structures.

### Data Extraction Features:

- **Test Case Metadata**: Automatically parses test case names to extract:
  - App Version (e.g., 2.81.0)
  - Tribe Short (e.g., FS)
  - Squad Name (e.g., Wealth)
  - OS Name (e.g., DANA+ & Reksadana)
  - Tribe Name (e.g., Financial Service)
  - Test Environment (e.g., SIT)
  - Platform (e.g., Android/iOS)
  - Test Case ID (e.g., NTC-44378)

- **Error Analysis**: Intelligent error summary extraction from test logs
- **Device Information**: Extracts device details, OS versions, and app information
- **Test Results**: Processes test outcomes and execution details
- **File Organization**: Maintains source file tracking and organization

### Output Formats:

- **CSV Files**: Structured data suitable for import into databases or spreadsheets
- **TXT Files**: Human-readable summaries organized by platform
- **Separate Files**: Option to create individual files per OS for better organization

## 🔧 Requirements

- Python 3.8 or higher (recommended: Python 3.10+)
- Required Python packages:
  - `python-dateutil` (for date parsing and normalization)
  - Standard libraries: `http.server`, `webbrowser`, `csv`, `os`, `re`, `datetime`, `shutil`, `sys`, `glob`, `json`, `io`

### Installation

```bash
# Install the only required external package
pip install python-dateutil
```

No other external dependencies required - the tool uses only built-in Python libraries for maximum compatibility.

## 📁 Input Format

The tool expects Markdown files from "History Archive Testcases" folders with the following structure:
- Test case files in `.md` format
- Structured test logs with consistent formatting
- Test case names following the expected naming convention

## 📋 Output Files

All output files are generated in the `md_extraction_results/` directory:

- `md_history_for_notion_import.csv` - Main CSV with all extracted data
- `md_history_for_notion_import_YYYYMMDD.csv` - Timestamped backup
- Platform-specific TXT files (if enabled):
  - `ios_summary.txt`
  - `android_summary.txt`
  - `combined_summary.txt`

## 🛠️ Customization

The tool can be modified to handle additional fields or adjust the extraction behavior based on your specific needs. Key functions for customization:

- `extract_test_properties()` - Test case name parsing
- `extract_error_summary()` - Error pattern matching
- `clean_description()` - Text cleaning and formatting

---

**Created:** May 23, 2025  
**Last Updated:** January 2025
