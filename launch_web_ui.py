#!/usr/bin/env python3
"""
Easy launcher for the MD File Processor Web UI
This script automatically launches the best available web interface.
"""

import sys
import os

def main():
    try:
        # Just run the script directly using subprocess
        import subprocess
        
        # Run extract_md_history.py with --web flag
        cmd = [sys.executable, 'extract_md_history.py', '--web']
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
