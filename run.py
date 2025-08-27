#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convenience script to run BiliDownload application.

This script provides an alternative way to launch the application
with proper path setup and error handling.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """
    Main function for running the application.
    
    Sets up the environment and launches the main application.
    """
    try:
        # Import logger manager
        from src.core.logger import get_logger
        
        # Get logger instance
        logger = get_logger("Run")
        
        # Import and launch main window
        from main import main as main_function
        main_function()
        
    except Exception as e:
        print(f"Failed to run application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 