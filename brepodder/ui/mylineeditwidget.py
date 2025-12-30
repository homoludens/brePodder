from PyQt5 import QtWidgets


class MyLineEdit(QtWidgets.QLineEdit):

    def __init__(self, parent=None):
        self.Parent = parent
        super(MyLineEdit, self).__init__(parent)

    def focusInEvent(self, event):
        super(MyLineEdit, self).clear()
        super(MyLineEdit, self).focusInEvent(event)




