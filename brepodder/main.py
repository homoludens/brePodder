#!/usr/bin/python
import os
import sys
from PyQt5 import QtWidgets
from config import DATA_DIR, ensure_data_dir
from logger import setup_logging, get_logger


if __name__ == "__main__":
    ensure_data_dir()
    os.chdir(str(DATA_DIR))
    
    # Initialize logging
    setup_logging()
    logger = get_logger("main")
    logger.info("Starting brePodder")
    
    # Import after logging is set up
    from brePodder import BrePodder

    app = QtWidgets.QApplication(sys.argv)
    ui = BrePodder(app)

    sys.exit(app.exec_())
