#!/usr/bin/env python3
# filepath: /Users/sariputray/dev/2023/submission-data/web_ui_cleaner.py

import csv
import re
import sys
import os
import webbrowser
import json
import http.server
import socketserver
import urllib.parse
import logging
from datetime import datetime
from threading import Thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('notion_data_cleaner')

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
def extract_test_properties(name):
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
    # Fixed pattern to correctly capture tribe names with various formats
    tribe_name_match = re.search(r'- ([A-Za-z]+(?: [A-Za-z&]+)*) \(', name)
    if tribe_name_match:
        properties['Tribe Name'] = tribe_name_match.group(1)
    
    # Extract Test Environment and Platform (e.g., SIT, Android)
    env_platform_match = re.search(r'\(([A-Za-z]+), ([A-Za-z]+)\)', name)
    if env_platform_match:
        properties['Test Environment'] = env_platform_match.group(1)
        properties['Platform'] = env_platform_match.group(2)
    
    # Extract Test Case Tag and Tag ID combined (e.g., NTC-44378)
    tag_id_match = re.search(r'- ([A-Z]+) - (\d+)', name)
    if tag_id_match:
        tag = tag_id_match.group(1)
        id_num = tag_id_match.group(2)
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

# Function to process file with historical data preservation
def process_historical_file(input_file):
    # Define output file paths
    base_name = os.path.basename(input_file)
    output_file = 'historical_data_for_notion_import.csv'
    output_file_with_date = f'historical_data_for_notion_import_{datetime.now().strftime("%Y%m%d")}.csv'
    
    # Check if input file exists
    if not os.path.exists(input_file):
        return {"status": "error", "message": f"Input file '{input_file}' not found!"}
    
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
        
        result_message = {
            "status": "success",
            "message": "Data cleaned successfully.",
            "stats": {
                "total_records": len(cleaned_rows)-1,
                "unique_test_cases": len(unique_ids),
                "output_file": output_file,
                "output_file_with_date": output_file_with_date,
                "original_file_size": os.path.getsize(input_file),
                "new_file_size": os.path.getsize(output_file),
                "size_change_percent": ((os.path.getsize(output_file)/os.path.getsize(input_file))*100)-100
            }
        }
        
        return result_message

    except Exception as e:
        return {"status": "error", "message": f"Error processing the CSV file: {str(e)}"}

# Create HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notion Test Data Cleaner</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: #fff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #1a3d66;
            text-align: center;
            margin-bottom: 30px;
        }
        .section {
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
        }
        .file-input-container {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .file-input-container input[type="text"] {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px 0 0 4px;
            background-color: #f9f9f9;
            font-size: 14px;
            cursor: pointer;  /* Changed from default to pointer */
            margin-right: -1px;
            height: 20px; /* Fixed height to align with button */
            line-height: 20px; /* Match line height */
            box-sizing: border-box; /* Ensure padding doesn't affect height */
        }
        .file-input-container .file-btn {
            padding: 10px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
            font-weight: 500;
            transition: background-color 0.2s;
            min-width: 80px;  /* Added to ensure button has minimum width */
            text-align: center;  /* Added to center the text */
            height: 40px; /* Fixed height to match input */
            box-sizing: border-box; /* Ensure padding doesn't affect height */
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .file-input-container .file-btn:hover {
            background-color: #3e8e41;
        }
        .options-container {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }
        .option {
            flex: 1;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .option:hover {
            background-color: #f0f7ff;
            border-color: #b3d7ff;
        }
        .option.selected {
            background-color: #e3f2fd;
            border-color: #2196F3;
            box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
        }
        .option-title {
            font-weight: 600;
            margin-bottom: 5px;
            color: #1a3d66;
        }
        .option-desc {
            font-size: 14px;
            color: #666;
        }
        .process-btn {
            display: block;
            width: 100%;
            padding: 12px;
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.3s;
            margin-top: 10px;
        }
        .process-btn:hover {
            background-color: #0b7dda;
        }
        .process-btn:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        .status-container {
            margin-top: 30px;
            padding: 20px;
            border-radius: 5px;
            background-color: #f9f9f9;
            border-left: 4px solid #ddd;
        }
        .status-title {
            font-weight: 600;
            margin-bottom: 10px;
            color: #333;
        }
        .status-content {
            font-family: monospace;
            white-space: pre-wrap;
            padding: 10px;
            background-color: #f1f1f1;
            border-radius: 4px;
            max-height: 200px;
            overflow-y: auto;
        }
        .success {
            border-left-color: #4CAF50;
        }
        .error {
            border-left-color: #f44336;
        }
        .processing {
            border-left-color: #2196F3;
        }
        .hide {
            display: none;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }
        .stat-item {
            padding: 10px;
            background-color: #e9f5fe;
            border-radius: 4px;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
        }
        .stat-value {
            font-weight: 600;
            color: #1a3d66;
            font-size: 16px;
        }
        .download-buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        .download-btn {
            flex: 1;
            padding: 10px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            font-weight: 500;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background-color 0.2s;
        }
        .download-btn:hover {
            background-color: #3e8e41;
        }
        .download-btn-dated {
            background-color: #2196F3;
        }
        .download-btn-dated:hover {
            background-color: #0b7dda;
        }
        .download-status {
            margin-top: 10px;
            font-size: 14px;
            font-style: italic;
            color: #666;
            text-align: center;
        }
        .download-progress {
            display: none;
            width: 100%;
            height: 4px;
            background-color: #f3f3f3;
            border-radius: 4px;
            margin-top: 10px;
            overflow: hidden;
        }
        .progress-bar {
            height: 100%;
            width: 0%;
            background-color: #4CAF50;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        footer {
            text-align: center;
            margin-top: 30px;
            color: #888;
            font-size: 12px;
        }
        #file-input {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Notion Test Data Cleaner</h1>
        
        <div class="section">
            <label for="csv-file">Select CSV File</label>
            <div class="file-input-container">
                <input type="text" id="file-display" placeholder="No file selected" readonly>
                <label for="file-input" class="file-btn">Browse</label>
                <input type="file" id="file-input" accept=".csv">
            </div>
        </div>
        
        <div class="section">
            <label>Processing Options</label>
            <div class="options-container">
                <div class="option selected" data-option="historical">
                    <div class="option-title">Preserve Historical Data</div>
                    <div class="option-desc">Keep all test runs while cleaning formatting</div>
                </div>
            </div>
        </div>
        
        <button id="process-btn" class="process-btn" disabled>Process File</button>
        
        <div id="status-container" class="status-container hide">
            <div class="status-title">Status</div>
            <div id="status-content" class="status-content">Select a CSV file to process</div>
            <div id="stats-container" class="stats-grid hide"></div>
            <div id="download-container" class="download-buttons hide">
                <a id="download-btn" class="download-btn" href="#" download>Download Processed File</a>
                <a id="download-dated-btn" class="download-btn download-btn-dated" href="#" download>Download With Date</a>
                <div id="download-progress" class="download-progress">
                    <div id="progress-bar" class="progress-bar"></div>
                </div>
                <div id="download-status" class="download-status"></div>
            </div>
        </div>
    </div>

    <footer>
        Created May 23, 2025 - Notion Test Case Data Cleaner
    </footer>

    <script>
        // Global variable to store the selected file
        let selectedFile = null;
        let selectedOption = 'historical';
        let processingComplete = false;
        
        // DOM elements
        const fileInput = document.getElementById('file-input');
        const fileDisplay = document.getElementById('file-display');
        const processBtn = document.getElementById('process-btn');
        const statusContainer = document.getElementById('status-container');
        const statusContent = document.getElementById('status-content');
        const statsContainer = document.getElementById('stats-container');
        const downloadContainer = document.getElementById('download-container');
        const downloadBtn = document.getElementById('download-btn');
        const downloadDatedBtn = document.getElementById('download-dated-btn');
        const downloadProgress = document.getElementById('download-progress');
        const progressBar = document.getElementById('progress-bar');
        const downloadStatus = document.getElementById('download-status');
        const options = document.querySelectorAll('.option');
        
        // Ensure download elements are hidden at startup
        downloadContainer.classList.add('hide');
        downloadProgress.style.display = 'none';
        
        // Event listener for file selection
        fileInput.addEventListener('change', function(e) {
            if (this.files.length > 0) {
                selectedFile = this.files[0];
                fileDisplay.value = selectedFile.name;
                processBtn.disabled = false;
                
                // Make sure download section is always hidden when a new file is selected
                downloadContainer.classList.add('hide');
                downloadProgress.style.display = 'none';
                downloadStatus.textContent = '';
                
                // Show status container but hide stats
                statusContainer.classList.remove('hide');
                statusContainer.classList.remove('success', 'error');
                statsContainer.classList.add('hide');
                statusContent.textContent = `File selected: ${selectedFile.name}\\nClick "Process File" to start processing.`;
            } else {
                resetFileSelection();
            }
        });
        
        // Event listener for file display input to trigger file input when clicked
        fileDisplay.addEventListener('click', function() {
            fileInput.click();
        });
        
        // Event listener for option selection
        options.forEach(option => {
            option.addEventListener('click', function() {
                options.forEach(opt => opt.classList.remove('selected'));
                this.classList.add('selected');
                selectedOption = this.dataset.option;
            });
        });
        
        // Event listener for process button
        processBtn.addEventListener('click', function() {
            if (!selectedFile) return;
            
            // Prepare form data for upload
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('option', selectedOption);
            
            // Update status and reset processing state
            processingComplete = false;
            statusContainer.classList.remove('success', 'error');
            statusContainer.classList.add('processing');
            statusContent.textContent = `Processing ${selectedFile.name}...`;
            statsContainer.classList.add('hide');
            downloadContainer.classList.add('hide');
            
            // Send the file to the server
            fetch('/process', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    statusContainer.classList.add('success');
                    statusContainer.classList.remove('processing', 'error');
                    processingComplete = true;
                    
                    // Display status message
                    statusContent.textContent = data.message;
                    
                    // Display statistics in a grid
                    statsContainer.innerHTML = '';
                    statsContainer.classList.remove('hide');
                    
                    const stats = data.stats;
                    for (const [key, value] of Object.entries(stats)) {
                        // Skip download URLs from display in stats grid
                        if (key === 'download_url' || key === 'download_date_url') {
                            continue;
                        }
                        
                        const statItem = document.createElement('div');
                        statItem.className = 'stat-item';
                        
                        const label = document.createElement('div');
                        label.className = 'stat-label';
                        label.textContent = key.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
                        
                        const statValue = document.createElement('div');
                        statValue.className = 'stat-value';
                        
                        // Format the value based on type
                        if (typeof value === 'number') {
                            if (key.includes('size')) {
                                statValue.textContent = formatBytes(value);
                            } else if (key.includes('percent')) {
                                statValue.textContent = value.toFixed(2) + '%';
                            } else {
                                statValue.textContent = value.toLocaleString();
                            }
                        } else {
                            statValue.textContent = value;
                        }
                        
                        statItem.appendChild(label);
                        statItem.appendChild(statValue);
                        statsContainer.appendChild(statItem);
                    }
                    
                    // Setup download buttons if URLs are available
                    if (stats.download_url) {
                        downloadBtn.href = stats.download_url;
                        downloadBtn.download = stats.output_file.split('/').pop();
                        
                        downloadDatedBtn.href = stats.download_date_url;
                        downloadDatedBtn.download = stats.output_file_with_date.split('/').pop();
                        
                        // Set up download event handlers
                        downloadBtn.onclick = function() {
                            initiateDownload(this, stats.output_file.split('/').pop());
                            return true; // Allow the default action to continue
                        };
                        
                        downloadDatedBtn.onclick = function() {
                            initiateDownload(this, stats.output_file_with_date.split('/').pop());
                            return true; // Allow the default action to continue
                        };
                        
                        downloadContainer.classList.remove('hide');
                    } else {
                        downloadContainer.classList.add('hide');
                    }
                } else {
                    statusContainer.classList.add('error');
                    statusContainer.classList.remove('processing', 'success');
                    processingComplete = false;
                    statusContent.textContent = data.message;
                    statsContainer.classList.add('hide');
                    downloadContainer.classList.add('hide');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                statusContainer.classList.add('error');
                statusContainer.classList.remove('processing', 'success');
                processingComplete = false;
                statusContent.textContent = `Error: ${error.message}`;
                statsContainer.classList.add('hide');
                downloadContainer.classList.add('hide');
            });
        });
        
        function resetFileSelection() {
            selectedFile = null;
            fileDisplay.value = '';
            processBtn.disabled = true;
            processingComplete = false;
            statusContainer.classList.add('hide');
            statsContainer.classList.add('hide');
            downloadContainer.classList.add('hide');
            downloadProgress.style.display = 'none';
            downloadStatus.textContent = '';
        }
        
        function formatBytes(bytes, decimals = 2) {
            if (bytes === 0) return '0 Bytes';
            
            const k = 1024;
            const dm = decimals < 0 ? 0 : decimals;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            
            return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
        }
        
        function initiateDownload(button, filename) {
            // Show download progress
            downloadProgress.style.display = 'block';
            progressBar.style.width = '0%';
            downloadStatus.textContent = `Starting download of ${filename}...`;
            
            // Simulate progress (since we can't track actual download progress from browser)
            let progress = 0;
            const interval = setInterval(() => {
                progress += 5;
                if (progress <= 90) {
                    progressBar.style.width = `${progress}%`;
                    downloadStatus.textContent = `Downloading ${filename}... ${progress}%`;
                }
                
                if (progress >= 90) {
                    clearInterval(interval);
                    // Complete the progress after a delay to simulate completion
                    setTimeout(() => {
                        progressBar.style.width = '100%';
                        downloadStatus.textContent = `${filename} downloaded successfully!`;
                        
                        // Hide progress bar after a few seconds
                        setTimeout(() => {
                            downloadProgress.style.display = 'none';
                        }, 3000);
                    }, 500);
                }
            }, 150);
        }
    </script>
</body>
</html>
"""

# Custom HTTP request handler
class DataCleanerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        elif self.path.startswith('/download/'):
            # Extract filename from path
            filename = self.path.split('/download/')[1]
            filename = urllib.parse.unquote(filename)
            
            logger.info(f"Download requested for file: {filename}")
            
            if os.path.exists(filename):
                try:
                    # Read the file content
                    with open(filename, 'rb') as f:
                        file_content = f.read()
                    
                    # Get the file size
                    file_size = len(file_content)
                    logger.info(f"Sending file {filename} ({file_size} bytes)")
                    
                    # Send the file to the client
                    self.send_response(200)
                    self.send_header('Content-type', 'text/csv')
                    self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(filename)}"')
                    self.send_header('Content-Length', str(file_size))
                    self.end_headers()
                    
                    # Write the file in chunks to support progress indication
                    chunk_size = 8192
                    for i in range(0, file_size, chunk_size):
                        end = min(i + chunk_size, file_size)
                        self.wfile.write(file_content[i:end])
                        
                except Exception as e:
                    # Log the error but don't expose details to the client
                    print(f"Error serving file {filename}: {str(e)}")
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b"Internal server error occurred while downloading the file")
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"File not found")
        else:
            super().do_GET()
            
    def do_POST(self):
        if self.path == '/process':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse multipart form data
            boundary = self.headers['Content-Type'].split('=')[1].encode()
            fields = self.parse_multipart(post_data, boundary)
            
            # Extract file and option
            file_content = fields.get('file', [b''])[0]
            option = fields.get('option', [b'historical'])[0].decode()
            
            # Write the uploaded file to a temporary location
            temp_file_path = 'temp_upload.csv'
            with open(temp_file_path, 'wb') as f:
                f.write(file_content)
            
            # Process the file based on the selected option
            if option == 'historical':
                result = process_historical_file(temp_file_path)
            else:
                result = {"status": "error", "message": "Invalid processing option"}
            
            # Add download URLs to the result
            if result['status'] == 'success':
                if 'output_file' in result['stats']:
                    result['stats']['download_url'] = f"/download/{urllib.parse.quote(result['stats']['output_file'])}"
                if 'output_file_with_date' in result['stats']:
                    result['stats']['download_date_url'] = f"/download/{urllib.parse.quote(result['stats']['output_file_with_date'])}"
            
            # Return the result as JSON
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        else:
            self.send_response(404)
            self.end_headers()
    
    def parse_multipart(self, data, boundary):
        fields = {}
        form_data = data.split(b'--' + boundary)
        
        # Process each form part
        for part in form_data:
            if b'Content-Disposition: form-data;' in part:
                # Extract field name
                name_match = re.search(b'name="([^"]+)"', part)
                if name_match:
                    name = name_match.group(1).decode()
                    
                    # Extract content (skip headers)
                    content_start = part.find(b'\r\n\r\n') + 4
                    content = part[content_start:].strip()
                    
                    # Add to fields
                    if name not in fields:
                        fields[name] = []
                    fields[name].append(content)
        
        return fields

# Start the web server
def start_server(port=8000):
    handler = DataCleanerHandler
    
    # Try to find an available port if the default is in use
    max_port_attempts = 10
    for attempt in range(max_port_attempts):
        try:
            httpd = socketserver.TCPServer(("", port), handler)
            break
        except OSError:
            if attempt < max_port_attempts - 1:
                print(f"Port {port} is in use, trying {port + 1}...")
                port += 1
            else:
                print(f"Could not find an available port after {max_port_attempts} attempts.")
                return
    
    print(f"Server running at http://localhost:{port}/")
    print("Press Ctrl+C to stop the server.")
    
    # Open web browser
    webbrowser.open(f'http://localhost:{port}/')
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("Shutting down server...")
        try:
            httpd.shutdown()
        except:
            pass

# Main entry point
if __name__ == "__main__":
    start_server()
