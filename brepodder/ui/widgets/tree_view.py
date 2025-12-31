"""
Custom TreeView widget with drag-and-drop support for organizing channels.
"""
from PyQt6 import QtCore, QtWidgets


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
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
        self.parent_widget = parent

    # Note: dropEvent, dropMimeData, dragEnterEvent are Qt overrides
    # and must keep their exact names to work correctly
    def dropEvent(self, event):
        """Handle drop events for drag-and-drop channel organization."""
        for selected_item in self.selectedItems():
            if (self.itemAt(event.position().toPoint()) is not None) and (self.itemAt(event.position().toPoint()).flags() & QtCore.Qt.ItemFlag.ItemIsDropEnabled):
                channel_title = selected_item.text(0)
                folder_title = self.itemAt(event.position().toPoint()).text(0)
            else:
                channel_title = selected_item.text(0)
                folder_title = None

            self.updateChannelList_db.emit(channel_title, folder_title)
        self.updateChannelList.emit()

    def dropMimeData(self, parent, row, data, action):
        """Handle MIME data drops."""
        if action == QtCore.Qt.DropAction.MoveAction:
            return self.moveSelection(parent, row)
        return False

    def dragEnterEvent(self, event):
        """Handle drag enter events."""
        event.accept()
