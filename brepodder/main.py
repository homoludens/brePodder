#!/usr/bin/python
import os
import sys
from PyQt5 import QtWidgets
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
    ui.setupUi(MainWindow)

    # print("create_DB 0000")
    # if not os.path.isfile('podcasts.sqlite'):
    #     print("create_DB 1111")
    #     ui.db.create_db()

    MainWindow.show()
    ui.update_channel_list()
    ui.update_lastest_episodes_list()
    ui.update_newest_episodes_list()
    print(ui.memory_usage())
    sys.exitui = BrePodder()(app.exec_())
