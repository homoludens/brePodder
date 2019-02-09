from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork #, QtWebKit
import sqlite3, os




#override QTreeViewWidget for handling Drag & Drop events
class treeViewWidget( QtWidgets.QTreeWidget ):

    updateChannelList = QtCore.pyqtSignal()
    updateChannelList_db = QtCore.pyqtSignal(str, str)

    def __init__(self, parent=None):
      super(treeViewWidget, self).__init__(parent)
      self.setAcceptDrops(True)
      self.setDragEnabled(True)
      self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
      self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
      self.sortByColumn(0, 0)
      self.Parent = parent

    def dropEvent(self, event):
        if self.itemAt( event.pos() ).flags() & QtCore.Qt.ItemIsDropEnabled:
            channelTitle = self.selectedItems()[0].text(0)
            folderTitle = self.itemAt(event.pos()).text(0)
        else:
            channelTitle = self.selectedItems()[0].text(0)
            folderTitle = None

        self.updateChannelList_db.emit(channelTitle,  folderTitle)
        self.updateChannelList.emit()


    def dropMimeData(self, parent, row, data, action):
        if action == QtCore.Qt.MoveAction:
            return self.moveSelection(parent, row)
        return False

    def dragEnterEvent(self, event):
            event.accept()
            print('drag')

