#!/usr/bin/python
# -*- coding: utf-8 -*-

#import vimpdb; vimpdb.set_trace()

from PyQt5 import QtCore, QtGui, QtWidgets #, QtNetwork #, QtWebKit
#, QtNetwork,  QtTest,  QtWebKit
import os, sys
#from getfavicon import getIcoUrl
#import opml
#import sys
#from sql import *
#from Ui_add_folder import *
#import feedparser

from brePodder import *

if __name__ == "__main__":
    os.chdir(os.path.expanduser('~'))

    if not os.path.isdir('.brePodder'):
        print(os.getcwd())
        os.makedirs('.brePodder')

    os.chdir('.brePodder')


    if not os.path.isdir('images'):
        print(os.getcwd())
        os.makedirs('images')

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = BrePodder()
#    baza = DBOperation()
    print(ui.memory_usage())
    ui.setupUi(MainWindow)

    print("create_DB 0000")
    if not os.path.isfile('podcasts.sqlite'):
        print("create_DB 1111")
        ui.db.create_DB()

    MainWindow.show()
    ui.update_channel_list()
    ui.update_lastest_episodes_list()
    ui.update_newest_episodes_list()
    print(ui.memory_usage())
    sys.exitui = BrePodder()(app.exec_())
