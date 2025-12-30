"""
Custom TreeView widget with drag-and-drop support for organizing channels.
"""
from PyQt5 import QtCore, QtWidgets


class TreeViewWidget(QtWidgets.QTreeWidget):
    """
    Override QTreeViewWidget for handling Drag & Drop events.
    
    Allows channels to be dragged into folders for organization.
    """

    updateChannelList = QtCore.pyqtSignal()
    updateChannelList_db = QtCore.pyqtSignal(str, str)

    def __init__(self, parent=None):
        super(TreeViewWidget, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.sortByColumn(0, 0)
        self.Parent = parent

    def dropEvent(self, event):
        for selectedItem in self.selectedItems():
            if (self.itemAt(event.pos()) is not None) and (self.itemAt(event.pos()).flags() & QtCore.Qt.ItemIsDropEnabled):
                channel_title = selectedItem.text(0)
                folder_title = self.itemAt(event.pos()).text(0)
            else:
                channel_title = selectedItem.text(0)
                folder_title = None

            self.updateChannelList_db.emit(channel_title, folder_title)
        self.updateChannelList.emit()

    def dropMimeData(self, parent, row, data, action):
        if action == QtCore.Qt.MoveAction:
            return self.moveSelection(parent, row)
        return False

    def dragEnterEvent(self, event):
        event.accept()
