#!/usr/bin/python
import os
import sys
from PyQt5 import QtWidgets
from brePodder import BrePodder
from config import DATA_DIR, ensure_data_dir


if __name__ == "__main__":
    ensure_data_dir()
    os.chdir(str(DATA_DIR))

    app = QtWidgets.QApplication(sys.argv)
    ui = BrePodder(app)

    sys.exit(app.exec_())
