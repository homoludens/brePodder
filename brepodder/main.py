#!/usr/bin/python
"""
brePodder - A PyQt5 podcast client.

This is the main entry point for the application.
"""
import os
import sys
from PyQt5 import QtWidgets, QtGui
from config import DATA_DIR, DEFAULT_FONT_SIZE, ensure_data_dir
from logger import setup_logging, get_logger


if __name__ == "__main__":
    ensure_data_dir()
    os.chdir(str(DATA_DIR))
    
    # Initialize logging
    setup_logging()
    logger = get_logger("main")
    logger.info("Starting brePodder")
    
    # Import after logging is set up
    from app import BrePodder
    from data.database import DBOperation

    app = QtWidgets.QApplication(sys.argv)
    
    # Apply font size setting
    db = DBOperation()
    font_size_str = db.getSetting('gui_font_size')
    if font_size_str:
        try:
            font_size = int(font_size_str)
            logger.info("Applying font size: %d pt", font_size)
            font = app.font()
            font.setPointSize(font_size)
            app.setFont(font)
        except ValueError:
            logger.warning("Invalid font size setting: %s, using default", font_size_str)
    else:
        logger.info("No font size setting found, using default (%d pt)", DEFAULT_FONT_SIZE)
        font = app.font()
        font.setPointSize(DEFAULT_FONT_SIZE)
        app.setFont(font)
    
    ui = BrePodder(app)

    sys.exit(app.exec_())
