from PyQt4 import QtCore, QtGui, QtNetwork, QtWebKit
#, QtNetwork,  QtTest,  QtWebKit
import os
#from getfavicon import getIcoUrl
from Download import *
import Image
#import opml
import re
from time import gmtime, strftime, mktime, sleep
#from elixir import *
#import sqlalchemy
import sys
import sqlite3
from sql import *
#from Ui_add_folder import *
import feedparser

import sys

from brePodder import *


if __name__ == "__main__":
    os.chdir(os.path.expanduser('~'))
    if not os.path.isdir('.brePodder'):
        os.makedirs('.brePodder')
    os.chdir('.brePodder')
#    os.makedirs('images')
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = BrePodder()
#    ui.setup(ui)
    baza = BaseOperation()
#    print ui.memory_usage()
    ui.setupUi(MainWindow)
    MainWindow.show()
    ui.update_channel_list()
    ui.update_lastest_episodes_list()
    ui.update_newest_episodes_list()
#    print ui.memory_usage()
    sys.exitui = BrePodder()(app.exec_())
