from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import feedparser

class FeedParserWorker(QObject):
    """Worker that does the heavy parsing in background thread"""
    parsing_finished = pyqtSignal(dict)  # Emits parsed feed data
    parsing_error = pyqtSignal(str)
    progress_update = pyqtSignal(str)  # Optional: status updates

    def __init__(self):
        super().__init__()
        self._is_running = True

    @pyqtSlot(str)
    def parse_feed(self, content):
        """This runs in the background thread"""
        try:
            self.progress_update.emit("Parsing feed...")

            # This is the blocking operation - now safe in worker thread
            feed = feedparser.parse(content)

            self.progress_update.emit("Parsing complete!")

            # Emit the result back to main thread
            self.parsing_finished.emit(feed)

        except Exception as e:
            self.parsing_error.emit(str(e))

    @pyqtSlot()
    def stop(self):
        self._is_running = False
