"""
Custom LineEdit widget that clears on focus.
"""
from PyQt6 import QtWidgets


class ClearOnFocusLineEdit(QtWidgets.QLineEdit):
    """
    A QLineEdit that clears its contents when focused.
    
    Used for input fields with placeholder-like behavior.
    """

    def __init__(self, parent=None):
        self.parent_widget = parent
        super(ClearOnFocusLineEdit, self).__init__(parent)

    # Note: focusInEvent is a Qt override and must keep its exact name
    def focusInEvent(self, event):
        """Clear the text when the widget receives focus."""
        super(ClearOnFocusLineEdit, self).clear()
        super(ClearOnFocusLineEdit, self).focusInEvent(event)


# Backward compatibility alias
MyLineEdit = ClearOnFocusLineEdit
