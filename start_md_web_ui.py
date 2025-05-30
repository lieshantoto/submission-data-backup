#!/usr/bin/env python3
"""
Launch the web UI for extract_md_history.py
"""
import sys
import os

if __name__ == "__main__":
    try:
        from md_extract_web_ui import start_server
        print("Starting MD Extract Web UI...")
        start_server()
    except ImportError:
        print("Error: md_extract_web_ui.py not found. Make sure it's in the same directory.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
