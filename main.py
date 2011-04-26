#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, QtNetwork, QtWebKit
#, QtNetwork,  QtTest,  QtWebKit
import os
#from getfavicon import getIcoUrl
#import opml
import sys
#from sql import *
#from Ui_add_folder import *
#import feedparser

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
#    baza = DBOperation()
#    print ui.memory_usage()
    ui.setupUi(MainWindow)
    
    if not os.path.isfile('podcasts.sqlite'):
        ui.db.create_DB()
    
    MainWindow.show()
    ui.update_channel_list()
    ui.update_lastest_episodes_list()
    ui.update_newest_episodes_list()
#    print ui.memory_usage()
    sys.exitui = BrePodder()(app.exec_())
