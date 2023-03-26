from PyQt5 import QtCore, QtGui, QtWidgets


class MyLineEdit(QtWidgets.QLineEdit):

    searchChannelList = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        self.Parent = parent
        super(MyLineEdit, self).__init__(parent)

    def focusInEvent(self, event):
        print('focus in event')
        # do custom stuff
        super(MyLineEdit, self).clear()
        super(MyLineEdit, self).focusInEvent(event)

    # def focusOutEvent(self, event) -> None:
    #     super(MyLineEdit, self).setText(QtWidgets.QApplication.translate("MainWindow", "Copy RSS or Youtube link", None))
    #     super(MyLineEdit, self).focusOutEvent(event)

    # def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
    #     self.searchChannelList.emit(self.text())
    #     super(MyLineEdit, self).keyReleaseEvent(event)




