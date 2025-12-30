"""
Audio player widget for brePodder.

Based on: https://github.com/pyqt/examples/blob/5225c0e7f070cc4496407c1ea565319be9274e29/src/pyqt-official/multimediawidgets/player.py
"""
import os
import signal
import subprocess
import sys
from typing import Optional

from PyQt5 import QtCore, QtMultimedia, QtWidgets
from utils.youtube import get_real_download_url, is_video_link, is_channel_url
from logger import get_logger

logger = get_logger(__name__)


class AudioPlayer(QtWidgets.QWidget):
    """
    An audio player widget with play/pause, seek, and download controls.
    
    Supports both built-in QMediaPlayer and external players (mpv, mplayer, etc.)
    """
    
    def __init__(self, url, parent=None):
        super(AudioPlayer, self).__init__(parent)
        logger.debug("AudioPlayer initialized with URL: %s", url)

        # External player process tracking
        self._external_process: Optional[subprocess.Popen] = None
        self._using_external: bool = False
        self._current_file: str = ""
        self._current_episode_id: Optional[int] = None
        self._db = None  # Will be set by parent app
        self._last_saved_position: int = 0

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(0, 1000)

        self.slider.sliderMoved.connect(self.set_position)
        self.slider.sliderMoved.connect(self.seek)
        self.duration = 0
        self.label_duration = QtWidgets.QLabel()

        QtWidgets.QWidget.__init__(self, parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        self.content = QtMultimedia.QMediaContent(QtCore.QUrl(url))

        self.player = QtMultimedia.QMediaPlayer()
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.player.setMedia(self.content)
        self.player.play()

        self.play_pause = QtWidgets.QPushButton(self)
        self.play_pause.setText("Play")
        self.play_pause.clicked.connect(self.play_clicked)
        self.player.stateChanged.connect(self.state_changed)

        self.stop_btn = QtWidgets.QPushButton(self)
        self.stop_btn.setText("Stop")
        self.stop_btn.clicked.connect(self.stop_clicked)

        self.slider.setRange(0, self.player.duration() // 1000)

        self.status = QtWidgets.QLabel(self)
        self.status.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.download = QtWidgets.QPushButton("Download", self)
        self.download.clicked.connect(self.fetch)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.play_pause)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.slider)
        layout.addWidget(self.label_duration)
        layout.addWidget(self.status)
        layout.addWidget(self.download)

    def seek(self, seconds):
        """Seek to a position in seconds."""
        self.player.setPosition(seconds * 1000)

    def duration_changed(self, duration):
        """Handle media duration change."""
        duration //= 1000

        self.duration = duration
        self.slider.setMaximum(duration)

    def position_changed(self, progress):
        """Handle playback position change."""
        progress //= 1000

        if not self.slider.isSliderDown():
            self.slider.setValue(progress)

        self.update_duration_info(progress)
        
        # Save position every 10 seconds
        if self._db and self._current_episode_id and progress - self._last_saved_position >= 10:
            self._last_saved_position = progress
            self._db.set_playback_position(self._current_episode_id, progress)

    def _on_media_status_changed(self, status):
        """Handle media status changes, particularly for seeking to saved position."""
        if status == QtMultimedia.QMediaPlayer.BufferedMedia or status == QtMultimedia.QMediaPlayer.LoadedMedia:
            if hasattr(self, '_pending_seek') and self._pending_seek:
                logger.debug("Seeking to saved position: %s seconds", self._pending_seek)
                self.player.setPosition(self._pending_seek * 1000)
                self._last_saved_position = self._pending_seek
                self._pending_seek = None
                # Disconnect to avoid repeated calls
                try:
                    self.player.mediaStatusChanged.disconnect(self._on_media_status_changed)
                except TypeError:
                    pass

    def update_duration_info(self, current_info):
        """Update the duration display label."""
        duration = self.duration
        if current_info or duration:
            current_time = QtCore.QTime((current_info//3600) % 60, (current_info//60) % 60, current_info % 60, (current_info * 1000) % 1000)
            total_time = QtCore.QTime((duration//3600) % 60, (duration//60) % 60, duration % 60, (duration*1000) % 1000)

            format_str = 'hh:mm:ss' if duration > 3600 else 'mm:ss'
            time_str = current_time.toString(format_str) + " / " + total_time.toString(format_str)
        else:
            time_str = ""

        self.label_duration.setText(time_str)

    def set_position(self, position):
        """Set the playback position."""
        self.player.setPosition(position)

    def set_url(self, url):
        """Set the media URL and start playback."""
        if is_video_link(url):
            url, duration = get_real_download_url(url, True)
        logger.debug("Setting media URL: %s", url)
        self._using_external = False
        self._current_file = url
        self.player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl(url)))
        self.player.play()
        self.status.setText("Built-in")

    def set_url_local(self, url, episode_id: Optional[int] = None):
        """Play a local file using built-in player."""
        self._using_external = False
        self._current_file = url
        self._current_episode_id = episode_id
        self._last_saved_position = 0
        uri = QtCore.QUrl.fromLocalFile(url)
        self.player.setMedia(QtMultimedia.QMediaContent(uri))
        
        # Seek to saved position if available
        if self._db and episode_id:
            saved_pos = self._db.get_playback_position(episode_id)
            if saved_pos > 0:
                # Need to wait for media to load before seeking
                self._pending_seek = saved_pos
                self.player.mediaStatusChanged.connect(self._on_media_status_changed)
            else:
                self._pending_seek = None
        
        self.player.play()
        self.status.setText("Built-in")

    def play_external(self, command: str, file_path: str) -> bool:
        """
        Play using an external player command.
        
        Args:
            command: The command to execute (with {file} already substituted)
            file_path: The file being played (for display/tracking)
            
        Returns:
            True if player started successfully, False otherwise
        """
        # Stop any currently playing content first
        self.stop_clicked()
        
        self._current_file = file_path
        self._using_external = True
        
        logger.info("Playing with external player: %s", command)
        try:
            self._external_process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid  # Create new process group for proper termination
            )
            self.play_pause.setText("Playing...")
            self.status.setText("External")
            
            # Start a timer to check if process is still running
            self._check_timer = QtCore.QTimer(self)
            self._check_timer.timeout.connect(self._check_external_process)
            self._check_timer.start(1000)  # Check every second
            
            return True
        except Exception as e:
            logger.error("Failed to start external player: %s", e)
            self._using_external = False
            self._external_process = None
            return False

    def _check_external_process(self):
        """Check if external process is still running."""
        if self._external_process is not None:
            poll = self._external_process.poll()
            if poll is not None:
                # Process has ended
                logger.debug("External player process ended with code: %s", poll)
                self._external_process = None
                self._using_external = False
                self.play_pause.setText("Play")
                self.status.setText("")
                if hasattr(self, '_check_timer'):
                    self._check_timer.stop()

    def enqueue(self, url):
        """Add media to the queue."""
        self.player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(url)))

    def play_clicked(self):
        """Handle play/pause button click."""
        if self._using_external:
            # For external players, we can try to send pause signal
            # but most CLI players don't support this well
            # So we just stop instead
            if self._external_process is not None:
                self.stop_clicked()
        else:
            if self.player.state() == QtMultimedia.QMediaPlayer.PlayingState:
                self.player.pause()
            else:
                self.player.play()

    def stop_clicked(self):
        """Stop all playback (both built-in and external)."""
        # Save current position before stopping
        if self._db and self._current_episode_id and not self._using_external:
            current_pos = self.player.position() // 1000
            if current_pos > 0:
                self._db.set_playback_position(self._current_episode_id, current_pos)
                logger.debug("Saved playback position: %s seconds for episode %s", 
                           current_pos, self._current_episode_id)
        
        # Stop built-in player
        self.player.stop()
        
        # Stop external player if running
        if self._external_process is not None:
            try:
                # Kill the entire process group
                os.killpg(os.getpgid(self._external_process.pid), signal.SIGTERM)
                self._external_process.wait(timeout=2)
            except (ProcessLookupError, subprocess.TimeoutExpired, OSError) as e:
                logger.debug("Error stopping external player: %s", e)
                try:
                    self._external_process.kill()
                except Exception:
                    pass
            finally:
                self._external_process = None
                self._using_external = False
        
        self.play_pause.setText("Play")
        self.status.setText("")
        if hasattr(self, '_check_timer'):
            self._check_timer.stop()

    def is_playing(self) -> bool:
        """Check if any playback is active."""
        if self._using_external:
            return self._external_process is not None and self._external_process.poll() is None
        else:
            return self.player.state() == QtMultimedia.QMediaPlayer.PlayingState

    def state_changed(self, new):
        """Handle player state change."""
        if not self._using_external:
            if new == QtMultimedia.QMediaPlayer.PlayingState:
                self.play_pause.setText("Pause")
            else:
                self.play_pause.setText("Play")

    def fetch(self):
        """Handle download button click."""
        logger.debug("Download requested for: %s", self._current_file)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = AudioPlayer("https://chtbl.com/track/4E942/audioboom.com/posts/7996900.mp3?modified=1647234100&source=rss&stitched=1")
    window.setWindowTitle("Audio Player")
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
