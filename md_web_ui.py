#!/usr/bin/env python3

"""
Simple web UI for extract_md_history.py
"""

import os
import sys
import webbrowser
import http.server
import socketserver
import json
import subprocess
import re
from threading import Thread

# HTML Template for the web interface
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MD File Processor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 {
            color: #4CAF50;
            text-align: center;
        }
        .container {
            background-color: #f5f5f5;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"] {
            width: 100%;
            padding: 8px;
            box-sizing: border-box;
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        .checkbox-group {
            margin-bottom: 15px;
        }
        .checkbox-option {
            margin-bottom: 8px;
        }
        .status {
            padding: 10px;
            border-radius: 4px;
            margin-top: 20px;
            display: none;
        }
        .processing {
            background-color: #e7f3fe;
            border: 1px solid #b6d4fe;
            color: #084298;
            display: block;
        }
        .success {
            background-color: #d1e7dd;
            border: 1px solid #badbcc;
            color: #0f5132;
            display: block;
        }
        .error {
            background-color: #f8d7da;
            border: 1px solid #f5c2c7;
            color: #842029;
            display: block;
        }
        .file-list {
            margin-top: 15px;
            background-color: #f8f9fa;
            padding: 10px;
            border: 1px solid #e9ecef;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1>MD File Processor</h1>
    
    <div class="container">
        <div class="form-group">
            <label for="folder-path">Folder Containing MD Files:</label>
            <div style="display: flex;">
                <input type="text" id="folder-path" readonly placeholder="Select a folder">
                <button id="browse-btn" style="margin-left: 10px;">Browse</button>
            </div>
        </div>
        
        <div class="checkbox-group">
            <label>Processing Options:</label>
            <div class="checkbox-option">
                <input type="checkbox" id="separate-csv">
                <label for="separate-csv">Create separate CSV files for each OS</label>
            </div>
            <div class="checkbox-option">
                <input type="checkbox" id="separate-txt">
                <label for="separate-txt">Create separate TXT files for each OS</label>
            </div>
            <div class="checkbox-option">
                <input type="checkbox" id="no-txt">
                <label for="no-txt">Skip TXT file generation completely</label>
            </div>
        </div>
        
        <button id="process-btn" disabled>Process Files</button>
    </div>
    
    <div id="status" class="status">
        Processing files...
    </div>
    
    <div id="output" class="file-list" style="display: none;">
        <h3>Generated Files:</h3>
        <ul id="file-list"></ul>
        <pre id="console-output" style="background-color: #eee; padding: 10px; max-height: 200px; overflow-y: auto;"></pre>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const folderPath = document.getElementById('folder-path');
            const browseBtn = document.getElementById('browse-btn');
            const processBtn = document.getElementById('process-btn');
            const separateCsv = document.getElementById('separate-csv');
            const separateTxt = document.getElementById('separate-txt');
            const noTxt = document.getElementById('no-txt');
            const status = document.getElementById('status');
            const output = document.getElementById('output');
            const fileList = document.getElementById('file-list');
            const consoleOutput = document.getElementById('console-output');
            
            // Handle browse button click
            browseBtn.addEventListener('click', function() {
                fetch('/browse')
                    .then(response => response.json())
                    .then(data => {
                        if (data.folder) {
                            folderPath.value = data.folder;
                            processBtn.disabled = false;
                        } else if (data.error) {
                            alert("Error: " + data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert("Error communicating with server");
                    });
            });
            
            // Handle no-txt checkbox to disable separate-txt
            noTxt.addEventListener('change', function() {
                if (this.checked) {
                    separateTxt.checked = false;
                    separateTxt.disabled = true;
                } else {
                    separateTxt.disabled = false;
                }
            });
            
            // Handle process button click
            processBtn.addEventListener('click', function() {
                if (!folderPath.value) {
                    alert("Please select a folder first");
                    return;
                }
                
                // Update status
                status.className = 'status processing';
                status.textContent = "Processing files...";
                output.style.display = 'none';
                fileList.innerHTML = '';
                consoleOutput.textContent = '';
                processBtn.disabled = true;
                
                // Build request data
                const requestData = {
                    folder: folderPath.value,
                    options: {
                        separateCsv: separateCsv.checked,
                        separateTxt: separateTxt.checked,
                        noTxt: noTxt.checked
                    }
                };
                
                // Send request to process files
                fetch('/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                })
                .then(response => response.json())
                .then(data => {
                    processBtn.disabled = false;
                    
                    if (data.success) {
                        // Show success status
                        status.className = 'status success';
                        status.textContent = "Processing completed successfully!";
                        
                        // Display output files
                        if (data.files && data.files.length > 0) {
                            output.style.display = 'block';
                            data.files.forEach(file => {
                                const li = document.createElement('li');
                                li.textContent = file;
                                fileList.appendChild(li);
                            });
                        }
                        
                        // Show console output
                        if (data.output) {
                            consoleOutput.textContent = data.output;
                        }
                    } else {
                        // Show error status
                        status.className = 'status error';
                        status.textContent = "Error: " + (data.error || "Unknown error");
                        
                        if (data.output) {
                            output.style.display = 'block';
                            consoleOutput.textContent = data.output;
                        }
                    }
                })
                .catch(error => {
                    processBtn.disabled = false;
                    status.className = 'status error';
                    status.textContent = "Error communicating with server: " + error.message;
                });
            });
        });
    </script>
</body>
</html>
"""

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence log messages
        pass
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        
        elif self.path == '/browse':
            folder = self._browse_folder()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(folder).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/process':
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            folder = data.get('folder', '')
            options = data.get('options', {})
            
            if not folder or not os.path.isdir(folder):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'Invalid folder path'
                }).encode())
                return
            
            # Process the folder
            result = self._process_folder(folder, options)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def _browse_folder(self):
        """Show folder selection dialog"""
        try:
            if sys.platform == 'darwin':  # macOS
                import subprocess
                cmd = '''osascript -e 'tell application "Finder" to set folderPath to choose folder with prompt "Select a folder containing MD files"' -e 'POSIX path of folderPath' '''
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                folder = proc.stdout.read().decode('utf-8').strip()
                return {'folder': folder} if folder else {'error': 'No folder selected'}
            
            elif sys.platform == 'win32':  # Windows
                import ctypes.wintypes
                import ctypes
                
                BIF_RETURNONLYFSDIRS = 0x0001
                BIF_USENEWUI = 0x0050
                
                ctypes.windll.ole32.CoInitialize(None)
                
                buffer = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                
                browseInfo = ctypes.Structure()
                browseInfo._fields_ = [
                    ("hwndOwner", ctypes.wintypes.HWND),
                    ("pidlRoot", ctypes.c_void_p),
                    ("pszDisplayName", ctypes.c_wchar_p),
                    ("lpszTitle", ctypes.c_wchar_p),
                    ("ulFlags", ctypes.c_uint),
                    ("lpfn", ctypes.c_void_p),
                    ("lParam", ctypes.c_longlong),
                    ("iImage", ctypes.c_int)
                ]
                
                browseInfo.lpszTitle = "Select a folder containing MD files"
                browseInfo.ulFlags = BIF_RETURNONLYFSDIRS | BIF_USENEWUI
                
                result = ctypes.windll.shell32.SHBrowseForFolderW(ctypes.byref(browseInfo))
                
                if result:
                    ctypes.windll.shell32.SHGetPathFromIDListW(result, buffer)
                    ctypes.windll.ole32.CoTaskMemFree(result)
                    folder = buffer.value
                    return {'folder': folder} if folder else {'error': 'No folder selected'}
                return {'error': 'No folder selected'}
            
            else:  # Linux and others
                try:
                    import subprocess
                    cmd = ['zenity', '--file-selection', '--directory', 
                           '--title=Select a folder containing MD files']
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    folder, _ = proc.communicate()
                    folder = folder.decode('utf-8').strip()
                    return {'folder': folder} if folder else {'error': 'No folder selected'}
                except:
                    return {'error': 'Folder selection not supported on this platform'}
        
        except Exception as e:
            print(f"Error selecting folder: {e}")
            return {'error': str(e)}
    
    def _process_folder(self, folder, options):
        """Process the selected folder with extract_md_history.py"""
        try:
            # Build command
            cmd = [sys.executable, 'extract_md_history.py', folder]
            
            if options.get('separateCsv'):
                cmd.append('--separate-csv')
            if options.get('separateTxt'):
                cmd.append('--separate-txt')
            if options.get('noTxt'):
                cmd.append('--no-txt')
            
            # Run the command
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode == 0:
                # Parse output to extract file information
                output_text = process.stdout
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
                
                # Remove duplicates and sort
                files_created = sorted(list(set(files_created)))
                
                return {
                    'success': True,
                    'files': files_created,
                    'output': output_text
                }
            else:
                return {
                    'success': False,
                    'error': process.stderr,
                    'output': process.stdout
                }
        
        except Exception as e:
            print(f"Error processing folder: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def start_server(port=8000):
    """Start the web server"""
    # Find an available port
    for p in range(port, port + 10):
        try:
            handler = RequestHandler
            httpd = socketserver.TCPServer(("", p), handler)
            server_url = f"http://localhost:{p}/"
            
            print(f"Starting web server at {server_url}")
            print("Press Ctrl+C to stop")
            
            # Open browser
            Thread(target=lambda: webbrowser.open(server_url)).start()
            
            # Start server
            httpd.serve_forever()
            return
        
        except OSError:
            print(f"Port {p} is in use, trying next port...")
    
    print("Could not find an available port")

if __name__ == "__main__":
    start_server()
