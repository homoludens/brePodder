# -*- coding: utf-8 -*-

import sys, os
from PyQt5 import QtCore, QtGui, uic
try:
	from PyQt5.phonon import Phonon
except:
	print "brePodder: No Phonon -> No Player!"
#import icons_rc

class AudioPlayer(QtGui.QWidget):
    def __init__(self, url, parent = None):

        self.url = url
        
        QtGui.QWidget.__init__(self, parent)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)

        self.player = Phonon.createPlayer(Phonon.MusicCategory, Phonon.MediaSource(url))
        self.player.setTickInterval(100)
        self.player.tick.connect(self.tock)

        self.play_pause = QtGui.QPushButton(self)
        #self.play_pause.setMinimumSize(QtCore.QSize(20,20))
        #self.play_pause.setMaximumSize(QtCore.QSize(50,25))
        #self.play_pause.setIcon(QtGui.QIcon(':/icons/player_play.svg'))
	self.play_pause.setText("Play")
        self.play_pause.clicked.connect(self.playClicked)
        self.player.stateChanged.connect(self.stateChanged)

        self.slider = Phonon.SeekSlider(self.player , self)
        
        self.status = QtGui.QLabel(self)
        self.status.setAlignment(QtCore.Qt.AlignRight |
            QtCore.Qt.AlignVCenter)
    
        self.download = QtGui.QPushButton("Download", self)
        self.download.clicked.connect(self.fetch)
        
        layout = QtGui.QHBoxLayout(self)
        layout.addWidget(self.play_pause)
        layout.addWidget(self.slider)
        layout.addWidget(self.status)
        layout.addWidget(self.download)

	self.setUrl("")

    def setUrl(self, url):
	#print url
	self.player.setCurrentSource( Phonon.MediaSource(url) )


    def enqueue(self, url):
	self.player.enqueue( Phonon.MediaSource(url) )


    def playClicked(self):
        if self.player.state() == Phonon.PlayingState:
            self.player.pause()
        else:
            self.player.play()
            
    def stateChanged(self, new, old):
        if new == Phonon.PlayingState:
            self.play_pause.setText("Pause")
        else:
            self.play_pause.setText("Play")

    def tock(self, time):
        time = time/1000
        h = time/3600
        m = (time-3600*h) / 60
        s = (time-3600*h-m*60)
	#print '%02d:%02d:%02d'%(h,m,s)
        #self.status.setText('%02d:%02d:%02d'%(h,m,s))
	#self.setWindowTitle('%02d:%02d:%02d'%(h,m,s))

    def fetch(self):
        print 'Should download %s'%self.url

def main():
    app = QtGui.QApplication(sys.argv)
    window=AudioPlayer(sys.argv[1])
    window.setWindowTitle("audio phonon")
    window.show()
    # It's exec_ because exec is a reserved word in Python
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
