"""
Settings dialog for brePodder.

Allows configuration of audio player and other preferences.
"""
from PyQt5 import QtCore, QtWidgets

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

    def saveSettings(self):
        """Save settings to database."""
        player_key = self.playerCombo.currentData()
        
        self.db.setSetting('player_type', player_key)
        self.db.setSetting('use_custom_player', 'true' if self.customPlayerCheck.isChecked() else 'false')
        self.db.setSetting('custom_play_command', self.customPlayCommand.text())
        self.db.setSetting('custom_enqueue_command', self.customEnqueueCommand.text())
        
        logger.info("Settings saved: player=%s, custom=%s", player_key, self.customPlayerCheck.isChecked())

    def applySettings(self):
        """Apply settings without closing dialog."""
        self.saveSettings()
        QtWidgets.QMessageBox.information(self, "Settings", "Settings applied successfully.")

    def accept(self):
        """Save settings and close dialog."""
        self.saveSettings()
        super().accept()
