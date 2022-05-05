import os
import sys

from PyQt5 import QtCore, QtMultimedia

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def main():
    # filename = os.path.join(CURRENT_DIR, "/home/homoludens/.brePodder/SecurityNowMP3/sn0700.mp3")
    filename = "/home/homoludens/.brePodder/SecurityNowMP3/sn0700.mp3"
    # url_remote = 'https://traffic.libsyn.com/secure/517c6bec-81cc-498a-86df-3a668eba6a93/CC0001_TheCatLadyAndThePetitioner.mp3'

    filename = os.path.abspath("/home/homoludens/.brePodder/SecurityNowMP3/sn0700.mp3")
    app = QtCore.QCoreApplication(sys.argv)

    player = QtMultimedia.QMediaPlayer()

    def handle_state_changed(state):
        if state == QtMultimedia.QMediaPlayer.PlayingState:
            print("started")
        elif state == QtMultimedia.QMediaPlayer.StoppedState:
            print("finished")
            QtCore.QCoreApplication.quit()

    player.stateChanged.connect(handle_state_changed)

    url = QtCore.QUrl.fromLocalFile(filename)
    # print(url)
    # url = QtCore.QUrl(url_remote)
    print(url)
    player.setMedia(QtMultimedia.QMediaContent(url))
    player.play()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()