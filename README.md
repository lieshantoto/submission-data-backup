# MD File Processor

A modern tool for processing test case data from Markdown files in the "History Archive Testcases" folder format.

## ✨ Features

- 🌐 **Modern Web Interface**: Clean, responsive UI for easy file processing
- 📁 **Smart Folder Selection**: 
  - Drag-and-drop your Notion export folder - automatically finds .md files anywhere in the folder structure
  - Browse button for precise folder selection with complex paths
- ⚙️ **Flexible Options**: 
  - Create separate CSV files for each OS
  - Generate separate TXT files for each OS  
  - Skip TXT generation entirely
  - Generate submission pass rate analysis
- 📊 **Real-time Processing**: See progress and results immediately
- 📋 **Multiple Output Formats**: CSV and TXT with detailed summaries
- 🔍 **Smart Data Extraction**: Automatically extracts test case metadata, error summaries, and device information
- 📈 **Pass Rate Analysis**: Generates submission-level pass rate tracking with cumulative progress

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

# Skip pass rate analysis
python3 extract_md_history.py "path/to/md/folder" --no-passrate
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
--passrate       # Generate pass rate analysis (default: enabled)
--no-passrate    # Skip pass rate analysis generation
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
- **Pass Rate Analysis**: Submission-level pass rate tracking with cumulative progress metrics

## 📈 Submission Pass Rate Analysis

The tool automatically generates a comprehensive pass rate analysis that tracks test submission progress over time.

### Features:

- **Cumulative Pass Tracking**: Shows progressive pass count from day 1 to each subsequent day
- **Unique Test Case Counting**: Counts only unique NTC-IDs per submission/platform combination
- **Daily Progress Metrics**: Pass rates calculated per submission day
- **Notion-Ready Format**: Clean CSV format optimized for Notion database import

### Pass Rate CSV Columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Name** | Submission identifier with app version, tribe, OS, and platform | `Submission 2.81.0 - FS Wealth - OS Insurance - Financial Service - Wealth (SIT iOS)` |
| **Total TC** | Total unique test cases (NTC-IDs) across all days | `253` |
| **Total Pass by Day** | Cumulative count of unique passed test cases up to this day | `122` |
| **Pass Rate** | Percentage of total test cases passed (Total Pass ÷ Total TC) | `0.482` |
| **Submission Day** | Date of the submission day | `May 21, 2025` |
| **OS Name** | Operating system/product area | `Insurance` |
| **Platform** | Testing platform | `iOS` |
| **App Version** | Application version | `2.81.0` |

### Example Output:

```csv
Name,Total TC,Total Pass by Day,Pass Rate,Submission Day,OS Name,Platform,App Version
Submission 2.81.0 - FS Wealth - OS Insurance - Financial Service - Wealth (SIT iOS),253,43,0.17,"May 19, 2025",Insurance,iOS,2.81.0
Submission 2.81.0 - FS Wealth - OS Insurance - Financial Service - Wealth (SIT iOS),253,78,0.31,"May 20, 2025",Insurance,iOS,2.81.0
Submission 2.81.0 - FS Wealth - OS Insurance - Financial Service - Wealth (SIT iOS),253,122,0.48,"May 21, 2025",Insurance,iOS,2.81.0
Submission 2.81.0 - FS Wealth - OS Insurance - Financial Service - Wealth (SIT iOS),253,253,1.00,"May 22, 2025",Insurance,iOS,2.81.0
```

### Benefits:

- **Progress Tracking**: Monitor testing progress day by day
- **Team Performance**: Analyze pass rates across different teams and platforms
- **Notion Integration**: Direct import into Notion databases with proper formatting
- **Historical Analysis**: Track testing efficiency and identify patterns

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

### Main Data Files:
- `historical_data_from_md_import_YYYYMMDD.csv` - Complete historical test data with metadata
- `submission_passrate_analysis_YYYYMMDD.csv` - Submission pass rate analysis for tracking progress

### Optional Additional Files:
- **Separate OS CSV Files** (if `--separate-csv` enabled):
  - `historical_data_from_md_import_YYYYMMDD_OS_[OSName].csv`
- **TXT Summary Files** (if TXT generation enabled):
  - `historical_data_from_md_import_YYYYMMDD.txt` - Combined summary
  - `historical_data_from_md_import_YYYYMMDD_OS_[OSName].txt` - OS-specific summaries (if `--separate-txt` enabled)
  - `historical_data_from_md_import_YYYYMMDD_summary.txt` - Overview summary (if `--separate-txt` enabled)

### File Naming Convention:
- `YYYYMMDD` format ensures chronological organization
- Timestamped files prevent accidental overwrites
- OS-specific files use sanitized names (spaces → underscores, special chars normalized)

## 🛠️ Customization

The tool can be modified to handle additional fields or adjust the extraction behavior based on your specific needs. Key functions for customization:

- `extract_test_properties()` - Test case name parsing
- `extract_error_summary()` - Error pattern matching
- `clean_description()` - Text cleaning and formatting
- `generate_passrate_analysis()` - Pass rate calculation and CSV generation

## 🆕 Recent Updates

### Version 2.1.0 (May 30, 2025)
- **Enhanced Pass Rate Analysis**: 
  - Fixed cumulative pass counting logic
  - Improved unique test case (NTC-ID) counting across all days
  - Added App Version column to pass rate CSV
  - Optimized CSV format for Notion import (removed unnecessary quotes)
- **Web UI Improvements**:
  - Fixed pass rate analysis file download functionality
  - Improved output file detection and parsing
  - Enhanced TXT generation checkbox behavior
- **Bug Fixes**:
  - Resolved duplicate pass rate file generation
  - Fixed TXT file generation when disabled
  - Improved error handling and file detection

### Key Improvements:
- **Accurate Metrics**: Total TC now counts unique NTC-IDs across all days per submission
- **Cumulative Tracking**: "Total Pass by Day" shows progressive accumulation of passed tests
- **Clean CSV Format**: Optimized for direct Notion database import
- **Better File Management**: Proper timestamping and organization of output files

## 🔧 Troubleshooting

### Common Issues:

**Q: Pass rate analysis file not appearing in download list**
- **Solution**: The latest version includes enhanced file detection. Ensure you're using the web interface and check the `md_extraction_results/` folder for `submission_passrate_analysis_*.csv` files.

**Q: TXT files being generated when checkbox is unchecked**
- **Solution**: This has been fixed in the latest version. The "Generate TXT files" checkbox now properly controls TXT file generation.

**Q: CSV import issues in Notion**
- **Solution**: The CSV format has been optimized with minimal quoting. Ensure the "App Version" column is set as a "Select" data type in your Notion database.

**Q: Cumulative pass counts seem incorrect**
- **Solution**: The pass rate calculation now properly counts unique NTC-IDs cumulatively across days. Each day shows the total unique test cases passed from day 1 through that day.

### File Locations:
- All output files are in: `md_extraction_results/`
- Main data: `historical_data_from_md_import_YYYYMMDD.csv`
- Pass rate analysis: `submission_passrate_analysis_YYYYMMDD.csv`

---

**Created:** May 23, 2025  
**Last Updated:** May 30, 2025
