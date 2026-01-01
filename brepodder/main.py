#!/usr/bin/python
"""
brePodder - A PyQt6 podcast client.

This is the main entry point for the application.
"""
import os
import sys
from PyQt6 import QtWidgets, QtGui
from config import DATA_DIR, DEFAULT_FONT_SIZE, ensure_data_dir
from logger import setup_logging, get_logger


if __name__ == "__main__":
    ensure_data_dir()
    os.chdir(str(DATA_DIR))

    # Initialize logging
    setup_logging(10)
    logger = get_logger("main")
    logger.info("Starting brePodder")

    # Import after logging is set up
    from app import BrePodder
    from data.database import DBOperation

    app = QtWidgets.QApplication(sys.argv)

    db = DBOperation()

    # Apply theme setting
    theme = db.getSetting('gui_theme') or 'system'
    logger.info("Applying theme: %s", theme)
    if theme == 'dark':
        app.setStyle('Fusion')
        dark_palette = QtGui.QPalette()
        dark_palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(255, 255, 255))
        dark_palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(35, 35, 35))
        dark_palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor(25, 25, 25))
        dark_palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor(255, 255, 255))
        dark_palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(255, 255, 255))
        dark_palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(255, 255, 255))
        dark_palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtGui.QColor(255, 0, 0))
        dark_palette.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor(42, 130, 218))
        dark_palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(42, 130, 218))
        dark_palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(35, 35, 35))
        dark_palette.setColor(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Text, QtGui.QColor(127, 127, 127))
        dark_palette.setColor(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(127, 127, 127))
        app.setPalette(dark_palette)
    elif theme == 'light':
        app.setStyle('Fusion')
        light_palette = QtGui.QPalette()
        light_palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(240, 240, 240))
        light_palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(0, 0, 0))
        light_palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(255, 255, 255))
        light_palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(245, 245, 245))
        light_palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor(255, 255, 220))
        light_palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor(0, 0, 0))
        light_palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(0, 0, 0))
        light_palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(240, 240, 240))
        light_palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(0, 0, 0))
        light_palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtGui.QColor(255, 0, 0))
        light_palette.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor(0, 100, 200))
        light_palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(0, 120, 215))
        light_palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(255, 255, 255))
        app.setPalette(light_palette)
    # else: 'system' - use default system theme

    # Apply font size setting
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

    sys.exit(app.exec())
