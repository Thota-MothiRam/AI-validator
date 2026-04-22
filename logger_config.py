

import os
import logging
import sys
from datetime import datetime

class TraceLogger:
    """A wrapper to provide trace.info, trace.error, etc. with correct stack tracing."""
    def __init__(self, logger):
        self.logger = logger

    def info(self, msg, *args, **kwargs):
        # stacklevel=2 tells Python to report the file that CALLED this function
        self.logger.info(msg, *args, stacklevel=2, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, stacklevel=2, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, stacklevel=2, **kwargs)



def setup_logging(name="lead_system"):
    """
    Sets up a unified logger with absolute paths to ensure log files
    are created in the project directory.
    """
    # 1. Determine the Absolute Path of the project root
    # This ensures logs go to /your_project/logs/ regardless of where you start the app
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "logs")
    
    if not os.path.exists(log_dir): 
        os.makedirs(log_dir)
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_filepath = os.path.join(log_dir, f"{current_date}_trace.log")

    # # 2. Define the Log Format
    # log_format = logging.Formatter('%(asctime)s - [%(name)s] - %(levelname)s - %(message)s')
    # To this (adding %(module)s):
    log_format = logging.Formatter('%(asctime)s - [%(module)s] - %(levelname)s - %(message)s')

    # 3. Get/Create the Logger instance
    base_logger = logging.getLogger(name)
    base_logger.setLevel(logging.INFO)

    # 4. Check if handlers already exist to prevent duplicate logs in Flask Debug mode
    if not base_logger.handlers:
        # File Handler (Writes to the .log file)
        # mode='a' ensures it appends to the file instead of overwriting it
        file_handler = logging.FileHandler(log_filepath, mode='a', encoding='utf-8')
        file_handler.setFormatter(log_format)
        file_handler.setLevel(logging.INFO)

        # Add handlers to the logger
        base_logger.addHandler(file_handler)
      

        # CRITICAL for Flask: Stop logs from "bubbling up" to the root logger
        # which can cause duplicate output or silent failures.
        base_logger.propagate = False

    return TraceLogger(base_logger)



