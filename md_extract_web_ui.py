#!/usr/bin/env python3
"""
Web UI module for extract_md_history.py
"""
import os
import sys
import json
import http.server
import socketserver
import webbrowser
import re
import logging
import urllib.parse
import subprocess
from threading import Thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('md_extract_web_ui')

# HTML template for the web interface
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MD File Processor</title>
    <style>
        /* Global styles */
        :root {
            --primary-color: #4caf50;
            --secondary-color: #2196f3;
            --error-color: #f44336;
            --success-color: #4caf50;
            --bg-color: #f5f5f5;
            --card-bg: #ffffff;
            --text-color: #333333;
            --border-color: #dddddd;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        header {
            margin-bottom: 30px;
            text-align: center;
        }
        
        h1 {
            color: var(--primary-color);
            margin-bottom: 10px;
        }
        
        /* Card styles */
        .card {
            background-color: var(--card-bg);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 25px;
        }
        
        .card-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 15px;
            color: var(--primary-color);
            display: flex;
            align-items: center;
        }
        
        .card-title .icon {
            margin-right: 8px;
            color: var(--primary-color);
        }
        
        /* Form controls */
        .form-control {
            margin-bottom: 16px;
        }
        
        .form-control label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }
        
        .input-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        input[type="text"] {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 0.9rem;
            background-color: #f9f9f9;
            cursor: pointer;
        }
        
        button {
            padding: 10px 20px;
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 0.9rem;
            cursor: pointer;
            transition: background-color 0.2s ease;
            white-space: nowrap;
        }
        
        button:hover {
            background-color: #43a047;
        }
        
        button:disabled {
            background-color: #9e9e9e;
            cursor: not-allowed;
        }
        
        /* Options section */
        .options-section {
            margin-bottom: 16px;
        }
        
        .options-title {
            font-weight: 500;
            margin-bottom: 12px;
        }
        
        .options-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .checkbox-option {
            display: flex;
            align-items: center;
            margin-right: 20px;
        }
        
        .checkbox-option input {
            margin-right: 8px;
        }
        
        /* Status display */
        .status-container {
            padding: 16px;
            border-radius: 6px;
            margin-top: 20px;
            display: none;
        }
        
        .processing {
            background-color: #e3f2fd;
            border: 1px solid #bbdefb;
            color: #1976d2;
            display: flex;
        }
        
        .success {
            background-color: #e8f5e9;
            border: 1px solid #c8e6c9;
            color: var(--success-color);
            display: block;
        }
        
        .error {
            background-color: #ffebee;
            border: 1px solid #ffcdd2;
            color: var(--error-color);
            display: block;
        }
        
        .spinner {
            border: 3px solid rgba(0, 0, 0, 0.1);
            border-radius: 50%;
            border-top: 3px solid var(--primary-color);
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* File output display */
        .file-list {
            margin-top: 16px;
            padding: 12px;
            background-color: #f5f5f5;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
            display: none;
        }
        
        .file-list h3 {
            margin-top: 0;
            font-size: 1rem;
            color: #555;
        }
        
        .file-list ul {
            margin: 0;
            padding-left: 20px;
        }
        
        .file-list li {
            margin-bottom: 6px;
            word-break: break-all;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>MD File Processor</h1>
            <p>Extract test case data from MD files in a folder</p>
        </header>
        
        <div class="card">
            <div class="card-title">
                <i class="icon">📁</i> Select MD Files Folder
            </div>
            
            <div class="form-control">
                <label for="folderPath">Folder Path</label>
                <div class="input-group">
                    <input type="text" id="folderPath" readonly placeholder="Click to select folder" />
                    <button id="browseBtn">Browse</button>
                </div>
            </div>
            
            <div class="options-section">
                <div class="options-title">Processing Options</div>
                <div class="options-grid">
                    <div class="checkbox-option">
                        <input type="checkbox" id="separateCsv" name="separateCsv" value="true">
                        <label for="separateCsv">Create separate CSV files for each OS</label>
                    </div>
                    <div class="checkbox-option">
                        <input type="checkbox" id="separateTxt" name="separateTxt" value="true">
                        <label for="separateTxt">Create separate TXT files for each OS</label>
                    </div>
                    <div class="checkbox-option">
                        <input type="checkbox" id="noTxt" name="noTxt" value="true">
                        <label for="noTxt">Skip TXT file generation completely</label>
                    </div>
                </div>
            </div>
            
            <button id="processBtn" disabled>Process MD Files</button>
            
            <div id="statusContainer" class="status-container">
                <div id="spinner" class="spinner"></div>
                <div id="statusContent"></div>
            </div>
            
            <div id="fileList" class="file-list">
                <h3>Output Files</h3>
                <ul id="outputFiles"></ul>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const folderPathInput = document.getElementById('folderPath');
            const browseBtn = document.getElementById('browseBtn');
            const processBtn = document.getElementById('processBtn');
            const separateCsvCheck = document.getElementById('separateCsv');
            const separateTxtCheck = document.getElementById('separateTxt');
            const noTxtCheck = document.getElementById('noTxt');
            const statusContainer = document.getElementById('statusContainer');
            const spinner = document.getElementById('spinner');
            const statusContent = document.getElementById('statusContent');
            const fileList = document.getElementById('fileList');
            const outputFiles = document.getElementById('outputFiles');
            
            let folderPath = '';
            
            // Event listener for browse button
            browseBtn.addEventListener('click', function() {
                fetch('/browse-folder')
                    .then(response => response.json())
                    .then(data => {
                        if (data.folderPath) {
                            folderPath = data.folderPath;
                            folderPathInput.value = folderPath;
                            processBtn.disabled = false;
                        } else {
                            console.error('Error:', data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                    });
            });
            
            // Handle checkbox relationships
            noTxtCheck.addEventListener('change', function() {
                if (this.checked) {
                    separateTxtCheck.checked = false;
                    separateTxtCheck.disabled = true;
                } else {
                    separateTxtCheck.disabled = false;
                }
            });
            
            // Event listener for process button
            processBtn.addEventListener('click', function() {
                if (!folderPath) return;
                
                // Get processing options
                const options = {
                    folderPath: folderPath,
                    separateCsv: separateCsvCheck.checked,
                    separateTxt: separateTxtCheck.checked,
                    noTxt: noTxtCheck.checked
                };
                
                // Update status
                statusContainer.className = 'status-container processing';
                spinner.style.display = 'block';
                statusContent.textContent = 'Processing MD files...';
                fileList.style.display = 'none';
                outputFiles.innerHTML = '';
                
                // Send request to process the folder
                fetch('/process-folder', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(options)
                })
                .then(response => response.json())
                .then(data => {
                    spinner.style.display = 'none';
                    
                    if (data.success) {
                        statusContainer.className = 'status-container success';
                        statusContent.textContent = data.message;
                        
                        // Display output files
                        if (data.files && data.files.length > 0) {
                            fileList.style.display = 'block';
                            data.files.forEach(file => {
                                const li = document.createElement('li');
                                li.textContent = file;
                                outputFiles.appendChild(li);
                            });
                        }
                    } else {
                        statusContainer.className = 'status-container error';
                        statusContent.textContent = data.message || 'An error occurred during processing.';
                    }
                })
                .catch(error => {
                    spinner.style.display = 'none';
                    statusContainer.className = 'status-container error';
                    statusContent.textContent = 'Error: ' + error.message;
                });
            });
        });
    </script>
</body>
</html>
"""

# Custom HTTP request handler
class MdExtractHandler(http.server.SimpleHTTPRequestHandler):
    # Silence server logs
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        elif self.path == '/browse-folder':
            if sys.platform == 'darwin':  # macOS
                # Use applescript to show folder selection dialog
                try:
                    import subprocess
                    cmd = '''osascript -e 'tell application "Finder" to set folderPath to choose folder with prompt "Select a folder containing MD files"' -e 'POSIX path of folderPath' '''
                    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                    folder_path = proc.stdout.read().decode('utf-8').strip()
                    
                    if folder_path:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'folderPath': folder_path}).encode())
                    else:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': 'No folder selected'}).encode())
                except Exception as e:
                    logger.error(f"Error opening folder dialog: {e}", exc_info=True)
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': str(e)}).encode())
            elif sys.platform == 'win32':  # Windows
                try:
                    import ctypes.wintypes as wintypes
                    import ctypes
                    
                    BIF_RETURNONLYFSDIRS = 0x0001
                    BIF_USENEWUI = 0x0050
                    
                    ctypes.windll.ole32.CoInitialize(None)
                    
                    buffer = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
                    bi = ctypes.Structure()
                    bi._fields_ = [
                        ("hwndOwner", wintypes.HWND),
                        ("pidlRoot", ctypes.c_void_p),
                        ("pszDisplayName", ctypes.c_wchar_p),
                        ("lpszTitle", ctypes.c_wchar_p),
                        ("ulFlags", ctypes.c_uint),
                        ("lpfn", ctypes.c_void_p),
                        ("lParam", ctypes.c_lparam),
                        ("iImage", ctypes.c_int)
                    ]
                    
                    bi.lpszTitle = "Select a folder containing MD files"
                    bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_USENEWUI
                    
                    result = ctypes.windll.shell32.SHBrowseForFolderW(ctypes.byref(bi))
                    
                    if result:
                        ctypes.windll.shell32.SHGetPathFromIDListW(result, buffer)
                        ctypes.windll.ole32.CoTaskMemFree(result)
                        folder_path = buffer.value
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'folderPath': folder_path}).encode())
                    else:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': 'No folder selected'}).encode())
                except Exception as e:
                    logger.error(f"Error opening folder dialog: {e}", exc_info=True)
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': str(e)}).encode())
            else:  # Linux and others
                try:
                    import subprocess
                    cmd = ['zenity', '--file-selection', '--directory', '--title=Select a folder containing MD files']
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    folder_path, error = proc.communicate()
                    folder_path = folder_path.decode('utf-8').strip()
                    
                    if folder_path:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'folderPath': folder_path}).encode())
                    else:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': 'No folder selected or zenity not installed'}).encode())
                except Exception as e:
                    logger.error(f"Error opening folder dialog: {e}", exc_info=True)
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/process-folder':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            folder_path = data.get('folderPath', '')
            separate_csv = data.get('separateCsv', False)
            separate_txt = data.get('separateTxt', False)
            no_txt = data.get('noTxt', False)
            
            if not folder_path or not os.path.isdir(folder_path):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False, 
                    'message': 'Invalid or missing folder path'
                }).encode())
                return
            
            try:
                # Build command to run extract_md_history.py
                cmd = [sys.executable, 'extract_md_history.py', folder_path]
                
                if separate_csv:
                    cmd.append('--separate-csv')
                if separate_txt:
                    cmd.append('--separate-txt')
                if no_txt:
                    cmd.append('--no-txt')
                
                logger.info(f"Running command: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Parse output to extract file information
                    output_text = result.stdout
                    files_created = []
                    
                    # Extract main CSV files
                    csv_matches = re.findall(r'written to ([\w\.-]+\.csv) and ([\w\.-]+\.csv)', output_text)
                    if csv_matches:
                        for match in csv_matches:
                            files_created.append(match[0])
                            files_created.append(match[1])
                    
                    # Extract separate CSV files
                    separate_csv_matches = re.findall(r'  - ([\w\.-_]+\.csv)', output_text)
                    files_created.extend(separate_csv_matches)
                    
                    # Extract TXT files
                    txt_files_matches = re.findall(r'TXT files created: ([\w\.-_]+\.txt) and ([\w\.-_]+\.txt)', output_text)
                    if txt_files_matches:
                        for match in txt_files_matches:
                            files_created.append(match[0])
                            files_created.append(match[1])
                    
                    # Extract summary files
                    summary_matches = re.findall(r'Summary files: ([\w\.-_]+\.txt) and ([\w\.-_]+\.txt)', output_text)
                    if summary_matches:
                        for match in summary_matches:
                            files_created.append(match[0])
                            files_created.append(match[1])
                    
                    # Remove duplicates and sort files
                    files_created = sorted(list(set(files_created)))
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': True,
                        'message': f"Successfully processed MD files from '{os.path.basename(folder_path)}' folder.",
                        'files': files_created,
                        'output': output_text
                    }).encode())
                else:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'message': f"Error processing MD files: {result.stderr}",
                        'error': result.stderr,
                        'output': result.stdout
                    }).encode())
            except Exception as e:
                logger.error(f"Error processing folder: {e}", exc_info=True)
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': f"Error: {str(e)}"
                }).encode())
        else:
            self.send_response(404)
            self.end_headers()


def start_server(port=8000):
    """Start the web server on the specified port"""
    handler = MdExtractHandler
    
    # Try to find an available port
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
                return None
    
    server_url = f"http://localhost:{port}/"
    print(f"Server running at {server_url}")
    print("Press Ctrl+C to stop the server.")
    
    # Open web browser in a separate thread to avoid blocking
    Thread(target=lambda: webbrowser.open(server_url)).start()
    
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
    
    return None

if __name__ == "__main__":
    start_server()
