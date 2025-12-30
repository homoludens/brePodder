"""
Settings dialog for brePodder.

Allows configuration of audio player and other preferences.
"""
from PyQt5 import QtCore, QtGui, QtWidgets

from config import DEFAULT_FONT_SIZE
from config_players import (
    PLAYERS,
    get_available_players,
    get_player_display_name,
)
from data.database import DBOperation
from logger import get_logger

logger = get_logger(__name__)


class SettingsDialog(QtWidgets.QDialog):
    """
    Settings dialog for configuring brePodder preferences.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DBOperation()
        self.setupUi()
        self.loadSettings()

    def setupUi(self):
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)

        # Player Settings Group
        player_group = QtWidgets.QGroupBox("Audio Player")
        player_layout = QtWidgets.QFormLayout(player_group)

        # Player selection combo box
        self.playerCombo = QtWidgets.QComboBox()
        self.populatePlayerCombo()
        self.playerCombo.currentIndexChanged.connect(self.onPlayerChanged)
        player_layout.addRow("Player:", self.playerCombo)

        # Player description
        self.playerDescription = QtWidgets.QLabel()
        self.playerDescription.setWordWrap(True)
        self.playerDescription.setStyleSheet("color: gray; font-style: italic;")
        player_layout.addRow("", self.playerDescription)

        # Custom player checkbox
        self.customPlayerCheck = QtWidgets.QCheckBox("Use custom player")
        self.customPlayerCheck.toggled.connect(self.onCustomPlayerToggled)
        player_layout.addRow("", self.customPlayerCheck)

        # Custom play command
        self.customPlayCommand = QtWidgets.QLineEdit()
        self.customPlayCommand.setPlaceholderText('e.g., mpv --no-video "{file}"')
        self.customPlayCommand.setEnabled(False)
        player_layout.addRow("Play command:", self.customPlayCommand)

        # Custom enqueue command
        self.customEnqueueCommand = QtWidgets.QLineEdit()
        self.customEnqueueCommand.setPlaceholderText('e.g., mpv --playlist-append="{file}"')
        self.customEnqueueCommand.setEnabled(False)
        player_layout.addRow("Enqueue command:", self.customEnqueueCommand)

        # Help text
        help_label = QtWidgets.QLabel(
            'Use {file} as placeholder for the file path or URL.\n'
            'Leave enqueue command empty if player does not support playlists.'
        )
        help_label.setStyleSheet("color: gray; font-size: 10px;")
        player_layout.addRow("", help_label)

        layout.addWidget(player_group)

        # GUI Settings Group
        gui_group = QtWidgets.QGroupBox("GUI Settings")
        gui_layout = QtWidgets.QFormLayout(gui_group)

        # Theme selection combo box
        self.themeCombo = QtWidgets.QComboBox()
        self.themeCombo.addItem("System Default", "system")
        self.themeCombo.addItem("Light", "light")
        self.themeCombo.addItem("Dark", "dark")
        gui_layout.addRow("Theme:", self.themeCombo)

        # Theme description
        theme_help = QtWidgets.QLabel("Select application color theme")
        theme_help.setStyleSheet("color: gray; font-size: 10px;")
        gui_layout.addRow("", theme_help)

        # Font size spinner
        self.fontSizeSpinner = QtWidgets.QSpinBox()
        self.fontSizeSpinner.setMinimum(8)
        self.fontSizeSpinner.setMaximum(24)
        self.fontSizeSpinner.setValue(DEFAULT_FONT_SIZE)
        self.fontSizeSpinner.setSuffix(" pt")
        gui_layout.addRow("Font size:", self.fontSizeSpinner)

        # Font size description
        font_help = QtWidgets.QLabel("Adjust the application font size")
        font_help.setStyleSheet("color: gray; font-size: 10px;")
        gui_layout.addRow("", font_help)

        layout.addWidget(gui_group)

        # Spacer
        layout.addStretch()

        # Button box
        self.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | 
            QtWidgets.QDialogButtonBox.Cancel |
            QtWidgets.QDialogButtonBox.Apply
        )
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self.applySettings)
        layout.addWidget(self.buttonBox)

    def populatePlayerCombo(self):
        """Populate the player combo box with available players."""
        available = get_available_players()
        
        for player_key in available:
            display_name = get_player_display_name(player_key)
            self.playerCombo.addItem(display_name, player_key)
        
        # Add "Custom" option at the end
        self.playerCombo.addItem("Custom...", "custom")

    def onPlayerChanged(self, index):
        """Handle player selection change."""
        player_key = self.playerCombo.currentData()
        
        if player_key == "custom":
            self.customPlayerCheck.setChecked(True)
            self.customPlayerCheck.setEnabled(False)
            self.playerDescription.setText("Configure your own player commands below.")
        else:
            self.customPlayerCheck.setEnabled(True)
            if not self.customPlayerCheck.isChecked():
                # Show description for selected player
                if player_key in PLAYERS:
                    desc = PLAYERS[player_key].get('description', '')
                    self.playerDescription.setText(desc)
                    
                    # Pre-fill custom commands with selected player's defaults
                    play_cmd = PLAYERS[player_key].get('play_command', '')
                    enqueue_cmd = PLAYERS[player_key].get('enqueue_command', '')
                    self.customPlayCommand.setText(play_cmd if play_cmd else '')
                    self.customEnqueueCommand.setText(enqueue_cmd if enqueue_cmd else '')

    def onCustomPlayerToggled(self, checked):
        """Handle custom player checkbox toggle."""
        self.customPlayCommand.setEnabled(checked)
        self.customEnqueueCommand.setEnabled(checked)
        
        if checked:
            self.playerDescription.setText("Enter custom commands below.")
        else:
            self.onPlayerChanged(self.playerCombo.currentIndex())

    def loadSettings(self):
        """Load settings from database."""
        # Load player type
        player_type = self.db.getSetting('player_type') or 'builtin'
        
        # Find and select the player in combo box
        index = self.playerCombo.findData(player_type)
        if index >= 0:
            self.playerCombo.setCurrentIndex(index)
        elif player_type == 'custom':
            index = self.playerCombo.findData('custom')
            if index >= 0:
                self.playerCombo.setCurrentIndex(index)
        
        # Load custom commands
        custom_play = self.db.getSetting('custom_play_command') or ''
        custom_enqueue = self.db.getSetting('custom_enqueue_command') or ''
        self.customPlayCommand.setText(custom_play)
        self.customEnqueueCommand.setText(custom_enqueue)
        
        # Check if using custom player
        use_custom = self.db.getSetting('use_custom_player') == 'true'
        self.customPlayerCheck.setChecked(use_custom)
        
        # Update UI state
        self.onPlayerChanged(self.playerCombo.currentIndex())
        
        # Load GUI settings
        font_size = self.db.getSetting('gui_font_size')
        if font_size:
            self.fontSizeSpinner.setValue(int(font_size))
        else:
            self.fontSizeSpinner.setValue(DEFAULT_FONT_SIZE)
        
        # Load theme setting
        theme = self.db.getSetting('gui_theme') or 'system'
        theme_index = self.themeCombo.findData(theme)
        if theme_index >= 0:
            self.themeCombo.setCurrentIndex(theme_index)

    def saveSettings(self):
        """Save settings to database."""
        player_key = self.playerCombo.currentData()
        
        self.db.setSetting('player_type', player_key)
        self.db.setSetting('use_custom_player', 'true' if self.customPlayerCheck.isChecked() else 'false')
        self.db.setSetting('custom_play_command', self.customPlayCommand.text())
        self.db.setSetting('custom_enqueue_command', self.customEnqueueCommand.text())
        
        # Save GUI settings
        self.db.setSetting('gui_font_size', str(self.fontSizeSpinner.value()))
        self.db.setSetting('gui_theme', self.themeCombo.currentData())
        
        logger.info("Settings saved: player=%s, custom=%s, font_size=%d, theme=%s", 
                    player_key, self.customPlayerCheck.isChecked(), self.fontSizeSpinner.value(),
                    self.themeCombo.currentData())

    def applyFontSize(self, size):
        """Apply the selected font size to the application."""
        app = QtWidgets.QApplication.instance()
        font = app.font()
        font.setPointSize(size)
        app.setFont(font)

    def applyTheme(self, theme):
        """Apply the selected theme to the application."""
        app = QtWidgets.QApplication.instance()
        if theme == 'dark':
            app.setStyle('Fusion')
            dark_palette = QtGui.QPalette()
            dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
            dark_palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(255, 255, 255))
            dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(35, 35, 35))
            dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
            dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(25, 25, 25))
            dark_palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(255, 255, 255))
            dark_palette.setColor(QtGui.QPalette.Text, QtGui.QColor(255, 255, 255))
            dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
            dark_palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(255, 255, 255))
            dark_palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 0, 0))
            dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
            dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
            dark_palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(35, 35, 35))
            dark_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtGui.QColor(127, 127, 127))
            dark_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, QtGui.QColor(127, 127, 127))
            app.setPalette(dark_palette)
        elif theme == 'light':
            app.setStyle('Fusion')
            light_palette = QtGui.QPalette()
            light_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(240, 240, 240))
            light_palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(0, 0, 0))
            light_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 255))
            light_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(245, 245, 245))
            light_palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(255, 255, 220))
            light_palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(0, 0, 0))
            light_palette.setColor(QtGui.QPalette.Text, QtGui.QColor(0, 0, 0))
            light_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(240, 240, 240))
            light_palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(0, 0, 0))
            light_palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 0, 0))
            light_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(0, 100, 200))
            light_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0, 120, 215))
            light_palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255))
            app.setPalette(light_palette)
        else:  # system
            app.setStyle('')
            app.setPalette(app.style().standardPalette())

    def applySettings(self):
        """Apply settings without closing dialog."""
        self.saveSettings()
        self.applyFontSize(self.fontSizeSpinner.value())
        self.applyTheme(self.themeCombo.currentData())
        QtWidgets.QMessageBox.information(self, "Settings", "Settings applied successfully.")

    def accept(self):
        """Save settings and close dialog."""
        self.saveSettings()
        self.applyFontSize(self.fontSizeSpinner.value())
        self.applyTheme(self.themeCombo.currentData())
        super().accept()
