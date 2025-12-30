"""
Custom LineEdit widget that clears on focus.
"""
from PyQt5 import QtWidgets


class MyLineEdit(QtWidgets.QLineEdit):
    """
    A QLineEdit that clears its contents when focused.
    
    Used for input fields with placeholder-like behavior.
    """

    def __init__(self, parent=None):
        self.Parent = parent
        super(MyLineEdit, self).__init__(parent)

    def focusInEvent(self, event):
        super(MyLineEdit, self).clear()
        super(MyLineEdit, self).focusInEvent(event)
