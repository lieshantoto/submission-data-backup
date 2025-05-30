#!/usr/bin/env python3
"""
Streamlit-like web UI for extract_md_history.py using only built-in Python libraries
This provides a clean, modern interface without requiring Streamlit installation.
"""

import os
import sys
import json
import http.server
import socketserver
import webbrowser
import subprocess
import re
import tempfile
from threading import Thread
from urllib.parse import urlparse, parse_qs

class StreamlitStyleHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence server logs
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_main_page().encode())
        elif self.path == '/browse-folder':
            self.handle_browse_folder()
        elif self.path.startswith('/download/'):
            self.handle_download()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/process':
            self.handle_process_files()
        else:
            self.send_response(404)
            self.end_headers()

    def get_main_page(self):
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MD File Processor</title>
    <style>
        /* Streamlit-inspired styling */
        :root {
            --primary-color: #ff6b6b;
            --secondary-color: #4ecdc4;
            --background: #ffffff;
            --surface: #fafafa;
            --text-primary: #262730;
            --text-secondary: #8e8ea0;
            --border: #e6eef3;
            --success: #00d4aa;
            --warning: #ffab00;
            --error: #ff6b6b;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Source Sans Pro', sans-serif;
            background: var(--background);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }

        .header {
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border-radius: 12px;
            color: white;
            box-shadow: 0 8px 32px rgba(255, 107, 107, 0.2);
        }

        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .card {
            background: var(--surface);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.08);
            border: 1px solid var(--border);
        }

        .section-title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--text-primary);
        }

        .input-group {
            display: flex;
            gap: 0.75rem;
            align-items: stretch;
        }

        input[type="text"] {
            flex: 1;
            padding: 0.75rem 1rem;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 1rem;
            background: white;
            transition: all 0.2s ease;
        }

        input[type="text"]:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(255, 107, 107, 0.1);
        }

        /* Drag and Drop Zone */
        .drop-zone {
            border: 3px dashed var(--border);
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            margin: 1rem 0;
            background: rgba(255, 107, 107, 0.02);
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            min-height: 120px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .drop-zone:hover {
            border-color: var(--primary-color);
            background: rgba(255, 107, 107, 0.05);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.15);
        }

        .drop-zone.drag-over {
            border-color: var(--primary-color);
            background: rgba(255, 107, 107, 0.1);
            transform: scale(1.02);
            box-shadow: 0 8px 25px rgba(255, 107, 107, 0.2);
            border-style: solid;
        }

        .drop-zone-content {
            pointer-events: none;
            width: 100%;
        }

        .drop-zone h3 {
            color: var(--primary-color);
            margin-bottom: 0.5rem;
            font-size: 1.2rem;
            font-weight: 600;
        }

        .drop-zone p {
            color: var(--text-secondary);
            margin: 0.5rem 0;
            line-height: 1.4;
        }

        .drop-zone .icon-large {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            opacity: 0.7;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 0.7; }
            50% { opacity: 1; }
            100% { opacity: 0.7; }
        }

        .drop-zone.drag-over .icon-large {
            animation: bounce 0.6s ease-in-out;
        }

        @keyframes bounce {
            0%, 20%, 60%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            80% { transform: translateY(-5px); }
        }
        }

        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
        }

        .btn-primary {
            background: var(--primary-color);
            color: white;
        }

        .btn-primary:hover:not(:disabled) {
            background: #ff5252;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
        }

        .btn-secondary {
            background: white;
            color: var(--text-primary);
            border: 2px solid var(--border);
        }

        .btn-secondary:hover {
            border-color: var(--primary-color);
            color: var(--primary-color);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }

        .options-grid {
            display: grid;
            gap: 1rem;
            margin-top: 1rem;
        }

        .process-section {
            text-align: center;
            padding: 1.5rem 0;
        }

        .process-section .btn-primary {
            font-size: 1.1rem;
            padding: 1rem 2rem;
            min-width: 200px;
        }

        .checkbox-option {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 1rem;
            background: white;
            border: 2px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .checkbox-option:hover {
            border-color: var(--primary-color);
            background: rgba(255, 107, 107, 0.05);
        }

        .checkbox-option input[type="checkbox"] {
            width: 1.2rem;
            height: 1.2rem;
            accent-color: var(--primary-color);
        }

        .checkbox-option label {
            margin: 0;
            cursor: pointer;
            font-weight: 500;
        }

        .status {
            padding: 1rem 1.5rem;
            border-radius: 8px;
            margin: 1.5rem 0;
            display: none;
            align-items: center;
            gap: 0.75rem;
        }

        .status.processing {
            background: rgba(78, 205, 196, 0.1);
            border: 2px solid var(--secondary-color);
            color: var(--secondary-color);
            display: flex;
        }

        .status.success {
            background: rgba(0, 212, 170, 0.1);
            border: 2px solid var(--success);
            color: var(--success);
            display: flex;
        }

        .status.error {
            background: rgba(255, 107, 107, 0.1);
            border: 2px solid var(--error);
            color: var(--error);
            display: flex;
        }

        .spinner {
            width: 1.2rem;
            height: 1.2rem;
            border: 2px solid rgba(78, 205, 196, 0.3);
            border-radius: 50%;
            border-top: 2px solid var(--secondary-color);
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .results {
            display: none;
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            border: 2px solid var(--success);
        }

        .results h3 {
            color: var(--success);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .file-list {
            list-style: none;
            padding: 0;
        }

        .file-list li {
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
        }

        .file-list li:last-child {
            border-bottom: none;
        }

        .file-info {
            flex: 1;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
            color: var(--text-primary);
        }

        .download-btn {
            padding: 0.5rem 1rem;
            background: var(--secondary-color);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
        }

        .download-btn:hover {
            background: #3bb7b1;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(78, 205, 196, 0.3);
        }

        .download-all-btn {
            margin-top: 1rem;
            padding: 0.75rem 1.5rem;
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            width: 100%;
            justify-content: center;
        }

        .download-all-btn:hover {
            background: #ff5252;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
        }

        .console-output {
            background: #f8f9fa;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 1rem;
            margin-top: 1rem;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.85rem;
            max-height: 200px;
            overflow-y: auto;
            white-space: pre-wrap;
            color: var(--text-secondary);
        }

        .icon {
            font-size: 1.2rem;
        }

        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .input-group {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 MD File Processor</h1>
            <p>Extract and analyze test case data from Markdown files</p>
        </div>

        <div class="card">
            <div class="section-title">
                <span class="icon">📁</span>
                Select Input Folder
            </div>
            
            <!-- Drag and Drop Zone -->
            <div id="dropZone" class="drop-zone">
                <div class="drop-zone-content">
                    <div class="icon-large">📁</div>
                    <h3>Drag & Drop Folder Here</h3>
                    <p>Or click anywhere in this area to browse</p>
                    <p><small>Drop a folder containing .md files from anywhere on your Mac</small></p>
                    <p><small><strong>Supported locations:</strong> Downloads, Desktop, Documents, and more</small></p>
                </div>
            </div>
            
            <div class="form-group">
                <label for="folderPath">Selected folder path:</label>
                <div class="input-group">
                    <input type="text" id="folderPath" readonly placeholder="No folder selected">
                    <button class="btn btn-secondary" id="browseBtn">
                        <span>📂</span> Browse
                    </button>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="section-title">
                <span class="icon">⚙️</span>
                Processing Options
            </div>
            
            <div class="options-grid">
                <div class="checkbox-option">
                    <input type="checkbox" id="separateCsv" name="separateCsv">
                    <label for="separateCsv">Create separate CSV files for each OS</label>
                </div>
                <div class="checkbox-option">
                    <input type="checkbox" id="generateTxt" name="generateTxt">
                    <label for="generateTxt">Generate TXT files (summary format)</label>
                </div>
                <div class="checkbox-option">
                    <input type="checkbox" id="separateTxt" name="separateTxt" disabled>
                    <label for="separateTxt">Create separate TXT files for each OS</label>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="process-section">
                <button class="btn btn-primary" id="processBtn" disabled>
                    <span>🚀</span> Process Files
                </button>
            </div>
            
            <div id="status" class="status">
                <div class="spinner"></div>
                <span id="statusText">Processing files...</span>
            </div>
            
            <div id="results" class="results">
                <h3>
                    <span>✅</span> Files Generated
                </h3>
                <ul id="fileList" class="file-list"></ul>
                <div id="consoleOutput" class="console-output"></div>
            </div>
        </div>
    </div>

    <script>
        const folderPathInput = document.getElementById('folderPath');
        const browseBtn = document.getElementById('browseBtn');
        const processBtn = document.getElementById('processBtn');
        const separateCsvCheck = document.getElementById('separateCsv');
        const generateTxtCheck = document.getElementById('generateTxt');
        const separateTxtCheck = document.getElementById('separateTxt');
        const status = document.getElementById('status');
        const statusText = document.getElementById('statusText');
        const results = document.getElementById('results');
        const fileList = document.getElementById('fileList');
        const consoleOutput = document.getElementById('consoleOutput');
        const dropZone = document.getElementById('dropZone');

        let selectedFolder = '';

        // Drag and Drop functionality
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            // Only remove drag-over if we're leaving the drop zone completely
            if (!dropZone.contains(e.relatedTarget)) {
                dropZone.classList.remove('drag-over');
            }
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');

            const items = e.dataTransfer.items;
            const files = e.dataTransfer.files;
            
            // Reset previous folder selection
            let folderFound = false;
            
            if (items && items.length > 0) {
                // Try to handle folders using webkit directory API
                for (let i = 0; i < items.length; i++) {
                    const item = items[i];
                    
                    if (item.kind === 'file') {
                        const entry = item.webkitGetAsEntry();
                        
                        if (entry && entry.isDirectory) {
                            // We found a folder - for web security, we can't get the full system path
                            // but we can work with the folder name and handle it on the server side
                            selectedFolder = entry.name;
                            folderPathInput.value = `📁 ${entry.name} (drag & drop folder)`;
                            processBtn.disabled = false;
                            folderFound = true;
                            
                            // Show success feedback
                            status.className = 'status success';
                            status.style.display = 'flex';
                            statusText.textContent = `Folder "${entry.name}" ready for processing (searching system locations...)`;
                            setTimeout(() => {
                                status.style.display = 'none';
                            }, 3000);
                            
                            break;
                        }
                    }
                }
            }
            
            // Fallback: Check if files were dropped and try to determine if they're from the same folder
            if (!folderFound && files && files.length > 0) {
                // Check if multiple files were dropped from the same directory
                const firstFile = files[0];
                if (firstFile.webkitRelativePath) {
                    // Files with webkitRelativePath suggest they came from a folder selection
                    const folderName = firstFile.webkitRelativePath.split('/')[0];
                    selectedFolder = folderName;
                    folderPathInput.value = `📁 ${folderName} (${files.length} files dropped)`;
                    processBtn.disabled = false;
                    folderFound = true;
                    
                    status.className = 'status success';
                    status.style.display = 'flex';
                    statusText.textContent = `Folder "${folderName}" with ${files.length} files ready for processing`;
                    setTimeout(() => {
                        status.style.display = 'none';
                    }, 3000);
                } else if (files.length > 1) {
                    // Multiple files without folder structure - show helpful message
                    status.className = 'status error';
                    status.style.display = 'flex';
                    statusText.textContent = 'Please drag the entire folder, not individual files';
                    setTimeout(() => {
                        status.style.display = 'none';
                    }, 3000);
                } else {
                    // Single file dropped
                    status.className = 'status error';
                    status.style.display = 'flex';
                    statusText.textContent = 'Please drag a folder containing .md files, not a single file';
                    setTimeout(() => {
                        status.style.display = 'none';
                    }, 3000);
                }
            }
            
            // If still no folder found, show generic error
            if (!folderFound && (!files || files.length === 0)) {
                status.className = 'status error';
                status.style.display = 'flex';
                statusText.textContent = 'No valid folder detected. Please try using the Browse button instead.';
                setTimeout(() => {
                    status.style.display = 'none';
                }, 3000);
            }
        });

        // Click on drop zone to trigger browse
        dropZone.addEventListener('click', () => {
            browseBtn.click();
        });

        // Browse button functionality
        browseBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/browse-folder');
                const data = await response.json();
                
                if (data.folderPath) {
                    selectedFolder = data.folderPath;
                    folderPathInput.value = data.folderPath;
                    processBtn.disabled = false;
                } else if (data.error) {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Error communicating with server: ' + error.message);
            }
        });

        // Checkbox interactions
        generateTxtCheck.addEventListener('change', () => {
            if (generateTxtCheck.checked) {
                separateTxtCheck.disabled = false;
            } else {
                separateTxtCheck.checked = false;
                separateTxtCheck.disabled = true;
            }
        });

        // Process button functionality
        processBtn.addEventListener('click', async () => {
            console.log('Process button clicked');
            console.log('Selected folder:', selectedFolder);
            
            if (!selectedFolder) {
                alert('Please select a folder first');
                return;
            }

            // Show processing status
            status.className = 'status processing';
            status.style.display = 'flex';
            statusText.textContent = 'Processing MD files...';
            results.style.display = 'none';
            processBtn.disabled = true;
            
            // Clear previous results
            fileList.innerHTML = '';
            consoleOutput.textContent = '';
            
            // Remove any existing download all buttons
            const existingDownloadAll = results.querySelector('.download-all-btn');
            if (existingDownloadAll && existingDownloadAll.parentElement) {
                existingDownloadAll.parentElement.remove();
            }

            const options = {
                folderPath: selectedFolder,
                separateCsv: separateCsvCheck.checked,
                separateTxt: separateTxtCheck.checked,
                noTxt: !generateTxtCheck.checked  // Inverse logic: if generateTxt is unchecked, skip TXT files
            };

            try {
                console.log('Sending request with options:', options);
                
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(options)
                });

                console.log('Response status:', response.status);
                const data = await response.json();
                console.log('Response data:', data);
                
                processBtn.disabled = false;

                if (data.success) {
                    status.className = 'status success';
                    statusText.textContent = 'Processing completed successfully!';
                    
                    // Show results
                    results.style.display = 'block';
                    fileList.innerHTML = '';
                    
                    if (data.files && data.files.length > 0) {
                        data.files.forEach(file => {
                            const li = document.createElement('li');
                            li.innerHTML = `
                                <span class="file-info">${file}</span>
                                <a href="/download/${file}" class="download-btn" download="${file}">
                                    📥 Download
                                </a>
                            `;
                            fileList.appendChild(li);
                        });
                        
                        // Add download all button
                        const downloadAllContainer = document.createElement('div');
                        downloadAllContainer.innerHTML = `
                            <button class="download-all-btn" onclick="downloadAllFiles([${data.files.map(f => `'${f}'`).join(',')}])">
                                📦 Download All Files
                            </button>
                        `;
                        results.appendChild(downloadAllContainer);
                    }
                    
                    if (data.output) {
                        consoleOutput.textContent = data.output;
                    }
                } else {
                    status.className = 'status error';
                    statusText.textContent = 'Error: ' + (data.message || 'Unknown error');
                    
                    if (data.output || data.error) {
                        results.style.display = 'block';
                        consoleOutput.textContent = data.output || data.error;
                    }
                }
            } catch (error) {
                processBtn.disabled = false;
                status.className = 'status error';
                statusText.textContent = 'Error: ' + error.message;
            }
        });
        
        // Download all files function
        function downloadAllFiles(fileNames) {
            if (!fileNames || fileNames.length === 0) {
                alert('No files to download');
                return;
            }
            
            // Download each file with a small delay to avoid overwhelming the browser
            fileNames.forEach((fileName, index) => {
                setTimeout(() => {
                    const link = document.createElement('a');
                    link.href = `/download/${fileName}`;
                    link.download = fileName;
                    link.style.display = 'none';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }, index * 500); // 500ms delay between downloads
            });
            
            // Show feedback
            status.className = 'status success';
            status.style.display = 'flex';
            statusText.textContent = `Downloading ${fileNames.length} files...`;
            setTimeout(() => {
                status.style.display = 'none';
            }, 3000);
        }
    </script>
</body>
</html>"""

    def handle_browse_folder(self):
        """Handle folder browsing request"""
        try:
            if sys.platform == 'darwin':  # macOS
                cmd = '''osascript -e 'tell application "Finder" to set folderPath to choose folder with prompt "Select folder containing MD files"' -e 'POSIX path of folderPath' '''
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                folder_path, error = proc.communicate()
                folder_path = folder_path.decode('utf-8').strip()
                
                if folder_path:
                    self.send_json_response({'folderPath': folder_path})
                else:
                    self.send_json_response({'error': 'No folder selected'})
            
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
                
                browseInfo.lpszTitle = "Select folder containing MD files"
                browseInfo.ulFlags = BIF_RETURNONLYFSDIRS | BIF_USENEWUI
                
                result = ctypes.windll.shell32.SHBrowseForFolderW(ctypes.byref(browseInfo))
                
                if result:
                    ctypes.windll.shell32.SHGetPathFromIDListW(result, buffer)
                    ctypes.windll.ole32.CoTaskMemFree(result)
                    folder_path = buffer.value
                    self.send_json_response({'folderPath': folder_path})
                else:
                    self.send_json_response({'error': 'No folder selected'})
            
            else:  # Linux and others
                try:
                    cmd = ['zenity', '--file-selection', '--directory', '--title=Select folder containing MD files']
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    folder_path, _ = proc.communicate()
                    folder_path = folder_path.decode('utf-8').strip()
                    
                    if folder_path:
                        self.send_json_response({'folderPath': folder_path})
                    else:
                        self.send_json_response({'error': 'No folder selected or zenity not installed'})
                except:
                    self.send_json_response({'error': 'Folder selection not supported on this platform'})
        
        except Exception as e:
            self.send_json_response({'error': str(e)})

    def handle_download(self):
        """Handle file download requests"""
        try:
            # Extract filename from path
            filename = self.path[10:]  # Remove '/download/' prefix
            
            # Security check: ensure filename doesn't contain path traversal
            if '..' in filename or '/' in filename or '\\' in filename:
                self.send_response(403)
                self.end_headers()
                return
            
            # Look for file in md_extraction_results directory
            results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'md_extraction_results')
            file_path = os.path.join(results_dir, filename)
            
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                self.send_response(404)
                self.end_headers()
                return
            
            # Determine content type based on file extension
            if filename.endswith('.csv'):
                content_type = 'text/csv'
            elif filename.endswith('.txt'):
                content_type = 'text/plain'
            else:
                content_type = 'application/octet-stream'
            
            # Send file
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(os.path.getsize(file_path)))
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error downloading file: {str(e)}".encode())

    def handle_process_files(self):
        """Handle file processing request"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            folder_path = data.get('folderPath', '')
            separate_csv = data.get('separateCsv', False)
            separate_txt = data.get('separateTxt', False)
            no_txt = data.get('noTxt', False)
            
            # Handle drag and drop folder names that don't have full paths
            if folder_path.startswith('📁 ') or not os.path.isabs(folder_path):
                # Extract folder name from the formatted display string
                if folder_path.startswith('📁 '):
                    if '(drag & drop folder)' in folder_path:
                        folder_name = folder_path.replace('📁 ', '').replace(' (drag & drop folder)', '').strip()
                    elif 'files dropped)' in folder_path:
                        folder_info = folder_path.replace('📁 ', '').strip()
                        folder_name = folder_info.split(' (')[0]
                    else:
                        folder_name = folder_path.replace('📁 ', '').strip()
                else:
                    folder_name = folder_path
                
                # Look for a folder with this name in the current directory first
                current_dir = os.path.dirname(os.path.abspath(__file__))
                potential_path = os.path.join(current_dir, folder_name)
                
                print(f"DEBUG: Looking for folder '{folder_name}'")
                print(f"DEBUG: Current dir: {current_dir}")
                print(f"DEBUG: Potential path: {potential_path}")
                print(f"DEBUG: Path exists: {os.path.exists(potential_path)}")
                print(f"DEBUG: Is directory: {os.path.isdir(potential_path)}")
                
                if os.path.isdir(potential_path):
                    folder_path = potential_path
                    print(f"DEBUG: Found folder at: {folder_path}")
                else:
                    # Search for folder in subdirectories (but limit depth to avoid long searches)
                    found_path = None
                    search_depth = 0
                    max_depth = 2
                    
                    for root, dirs, files in os.walk(current_dir):
                        # Calculate current depth
                        current_depth = root.replace(current_dir, '').count(os.sep)
                        if current_depth > max_depth:
                            continue
                            
                        if folder_name in dirs:
                            found_path = os.path.join(root, folder_name)
                            print(f"DEBUG: Found folder in subdirectory: {found_path}")
                            break
                    
                    if found_path:
                        folder_path = found_path
                    else:
                        # Search in common locations on Mac
                        search_locations = [
                            os.path.expanduser("~/Downloads"),
                            os.path.expanduser("~/Desktop"),
                            os.path.expanduser("~/Documents"),
                            "/Users",  # Search in all user directories
                            "/Volumes",  # External drives
                        ]
                        
                        print(f"DEBUG: Searching for folder '{folder_name}' in common locations...")
                        
                        for location in search_locations:
                            if not os.path.exists(location):
                                continue
                                
                            try:
                                # Direct check in the location
                                potential = os.path.join(location, folder_name)
                                if os.path.isdir(potential):
                                    folder_path = potential
                                    print(f"DEBUG: Found folder at: {folder_path}")
                                    break
                                
                                # Search in subdirectories (limit depth for performance)
                                for root, dirs, files in os.walk(location):
                                    # Limit search depth to avoid long searches
                                    depth = root.replace(location, '').count(os.sep)
                                    if depth > 3:  # Don't go too deep
                                        continue
                                    
                                    if folder_name in dirs:
                                        folder_path = os.path.join(root, folder_name)
                                        print(f"DEBUG: Found folder at: {folder_path}")
                                        break
                                
                                if folder_path and os.path.isdir(folder_path):
                                    break
                                    
                            except (PermissionError, OSError):
                                # Skip locations we can't access
                                continue
                        
                        if not folder_path or not os.path.isdir(folder_path):
                            self.send_json_response({
                                'success': False,
                                'message': f'Could not find folder "{folder_name}" in common locations (Downloads, Desktop, Documents, etc.). Please use the Browse button to select the folder with its full path.'
                            })
                            return
            
            if not folder_path or not os.path.isdir(folder_path):
                self.send_json_response({
                    'success': False,
                    'message': 'Invalid or missing folder path'
                })
                return
            
            # Build command to run extract_md_history.py
            cmd = [sys.executable, 'extract_md_history.py', folder_path]
            
            if separate_csv:
                cmd.append('--separate-csv')
            if separate_txt:
                cmd.append('--separate-txt')
            if no_txt:
                cmd.append('--no-txt')
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            if result.returncode == 0:
                # Parse output to extract file information
                output_text = result.stdout
                files_created = self.parse_output_files(output_text)
                
                self.send_json_response({
                    'success': True,
                    'message': f"Successfully processed MD files from '{os.path.basename(folder_path)}' folder.",
                    'files': files_created,
                    'output': output_text
                })
            else:
                self.send_json_response({
                    'success': False,
                    'message': f"Error processing MD files: {result.stderr}",
                    'error': result.stderr,
                    'output': result.stdout
                })
        
        except Exception as e:
            self.send_json_response({
                'success': False,
                'message': f"Error: {str(e)}"
            })

    def parse_output_files(self, output_text):
        """Parse the output text to extract created file names"""
        files_created = []
        
        # Extract main CSV files from lines like "📄 historical_data_from_md_import.csv"
        csv_matches = re.findall(r'📄 ([\w\.-_]+\.csv)', output_text)
        files_created.extend(csv_matches)
        
        # Extract TXT files from lines like "📝 TXT files created: historical_data_from_md_import.txt and historical_data_from_md_import_20250530.txt"
        txt_matches = re.findall(r'📝 TXT files created: ([\w\.-_]+\.txt) and ([\w\.-_]+\.txt)', output_text)
        if txt_matches:
            for match in txt_matches:
                files_created.append(match[0])
                files_created.append(match[1])
        
        # Also search for any file pattern that looks like our output files
        all_file_matches = re.findall(r'(historical_data_from_md_import[^,\s]*\.(?:csv|txt))', output_text)
        files_created.extend(all_file_matches)
        
        # Always include actual files from the directory to ensure we don't miss any
        try:
            results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'md_extraction_results')
            if os.path.exists(results_dir):
                all_files = os.listdir(results_dir)
                # Get all CSV and TXT files that match our naming pattern
                import time
                current_time = time.time()
                
                for filename in all_files:
                    if (filename.endswith(('.csv', '.txt')) and 
                        filename.startswith('historical_data_from_md_import') and 
                        not filename.startswith('.')):
                        file_path = os.path.join(results_dir, filename)
                        if os.path.isfile(file_path):
                            # Include recent files (last 10 minutes) or if no files found in output
                            file_time = os.path.getmtime(file_path)
                            if not files_created or (current_time - file_time < 600):  # 10 minutes
                                files_created.append(filename)
        except Exception as e:
            print(f"DEBUG: Error listing directory files: {e}")
        
        # Remove duplicates and sort
        unique_files = sorted(list(set(files_created)))
        print(f"DEBUG: Found files: {unique_files}")
        return unique_files

    def send_json_response(self, data):
        """Send a JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def start_server(port=8000):
    """Start the web server"""
    # Find an available port
    for p in range(port, port + 10):
        try:
            handler = StreamlitStyleHandler
            httpd = socketserver.TCPServer(("", p), handler)
            server_url = f"http://localhost:{p}/"
            
            print(f"🚀 Starting MD File Processor at {server_url}")
            print("📁 Ready to process Markdown files!")
            print("⏹️  Press Ctrl+C to stop the server")
            
            # Open browser in a separate thread
            Thread(target=lambda: webbrowser.open(server_url)).start()
            
            # Start server
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n👋 Shutting down server...")
                httpd.shutdown()
            return
        
        except OSError:
            print(f"Port {p} is in use, trying next port...")
    
    print("❌ Could not find an available port")


if __name__ == "__main__":
    start_server()
