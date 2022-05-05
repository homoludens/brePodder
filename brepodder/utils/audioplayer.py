# -*- coding: utf-8 -*-
"""
https://github.com/pyqt/examples/blob/5225c0e7f070cc4496407c1ea565319be9274e29/src/pyqt-official/multimediawidgets/player.py
"""
import sys
from PyQt5 import QtCore, QtGui, QtMultimedia, QtWidgets
from utils.youtube import get_real_download_url, is_video_link, is_channel_url


class AudioPlayer(QtWidgets.QWidget):
    def __init__(self, url, parent=None):
        super(AudioPlayer, self).__init__(parent)
        print("AudioPlayer")
        print(url)
        # url = 'https://traffic.libsyn.com/secure/517c6bec-81cc-498a-86df-3a668eba6a93/CC0001_TheCatLadyAndThePetitioner.mp3'
        # self.url = QtCore.QUrl(url)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(0, 1000)

        self.slider.sliderMoved.connect(self.setPosition)
        self.slider.sliderMoved.connect(self.seek)
        self.duration = 0
        self.labelDuration = QtWidgets.QLabel()

        QtWidgets.QWidget.__init__(self, parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        # self.content = QtCore.QUrl.fromLocalFile(url)
        self.content = QtMultimedia.QMediaContent(QtCore.QUrl(url))

        self.player = QtMultimedia.QMediaPlayer()
        self.player.positionChanged.connect(self.positionChanged)
        self.player.durationChanged.connect(self.durationChanged)
        self.player.setMedia(self.content)
        self.player.play()

        self.play_pause = QtWidgets.QPushButton(self)
        self.play_pause.setText("Play")
        self.play_pause.clicked.connect(self.playClicked)
        self.player.stateChanged.connect(self.stateChanged)

        self.slider.setRange(0, self.player.duration() // 1000)

        self.status = QtWidgets.QLabel(self)
        self.status.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.download = QtWidgets.QPushButton("Download", self)
        self.download.clicked.connect(self.fetch)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.play_pause)
        layout.addWidget(self.slider)
        layout.addWidget(self.labelDuration)
        layout.addWidget(self.status)
        layout.addWidget(self.download)

    def seek(self, seconds):
        self.player.setPosition(seconds * 1000)

    def durationChanged(self, duration):
        duration //= 1000

        self.duration = duration
        self.slider.setMaximum(duration)

    def positionChanged(self, progress):
        progress //= 1000

        if not self.slider.isSliderDown():
            self.slider.setValue(progress)

        self.updateDurationInfo(progress)

    def updateDurationInfo(self, currentInfo):
        duration = self.duration
        if currentInfo or duration:
            currentTime = QtCore.QTime((currentInfo//3600) % 60, (currentInfo//60) % 60, currentInfo % 60, (currentInfo * 1000) % 1000)
            totalTime = QtCore.QTime((duration//3600) % 60, (duration//60) % 60, duration % 60, (duration*1000) % 1000)

            format = 'hh:mm:ss' if duration > 3600 else 'mm:ss'
            tStr = currentTime.toString(format) + " / " + totalTime.toString(format)
        else:
            tStr = ""

        self.labelDuration.setText(tStr)

    def setPosition(self, position):
        self.player.setPosition(position)

    def setUrl(self, url):
        if is_video_link(url):
            url, duration = get_real_download_url(url, True)
        print(url)
        #print url
        self.player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl(url)))
        self.player.play()

    def setUrl_local(self, url):
        # QtCore.QUrl.setUrl()
        uri = QtCore.QUrl.fromLocalFile(url)
        self.player.setMedia(QtMultimedia.QMediaContent(uri))

    def enqueue(self, url):
        self.player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(url)))

    def playClicked(self):
        if self.player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def stateChanged(self, new):
        if new == QtMultimedia.QMediaPlayer.PlayingState:
            self.play_pause.setText("Pause")
        else:
            self.play_pause.setText("Play")

    def fetch(self):
        print('Should download %s' % self.url)


def main():
    app = QtWidgets.QApplication(sys.argv)
    # window = AudioPlayer(sys.argv[1])
    # window = AudioPlayer('/home/homoludens/.brePodder/SecurityNowMP3/sn0700.mp3')
    # window = AudioPlayer('https://traffic.libsyn.com/secure/517c6bec-81cc-498a-86df-3a668eba6a93/CC0001_TheCatLadyAndThePetitioner.mp3')
    window = AudioPlayer("https://chtbl.com/track/4E942/audioboom.com/posts/7996900.mp3?modified=1647234100&source=rss&stitched=1")
    window.setWindowTitle("Audio Player")
    window.show()
    # It's exec_ because exec is a reserved word in Python
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
