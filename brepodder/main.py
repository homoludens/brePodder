#!/usr/bin/python
import os
import sys
from PyQt5 import QtWidgets
from brePodder import *

if __name__ == "__main__":
    os.chdir(os.path.expanduser('~'))
    if not os.path.isdir('.brePodder'):
        os.makedirs('.brePodder')
    os.chdir('.brePodder')

    app = QtWidgets.QApplication(sys.argv)
    ui = BrePodder(app)

    sys.exit(app.exec_())
