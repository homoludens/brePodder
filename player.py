#!/usr/bin/python
# -*- coding: Utf-8 -*-

# widget mplayer en pyqt
# code python traduit du code c++ de http://doc.qtfr.org/public/2007/qt_mplayer.tar.gz

# Avec quelques modifs d'apres le code d'alteo_gange (http://forum.qtfr.org/viewtopic.php?pid=31501#p31501) :
# - le systeme est identifie automatiquement
# - le code fonctionne maintenant sous Windows
# - la connexion du signal finished a ete corrigee


import sys, os
from PyQt4.QtGui import *
from PyQt4.QtCore import *

if os.name in ['posix', 'mac']:
    mplayerPath="mplayer"    # moteur de lecture mplayer
elif os.name=='nt':
    mplayerPath="\"C:/Program Files/MPlayer-1.0rc2/mplayer.exe\"" # Ou un autre chemin. Attention, il faut bien mettre le ".exe"
movieFile="test.avi"    # chemin de la vidéo

class PlayerWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        
        self.isPlaying=False
        
        self.controller = QPushButton("Play")
        
        self.renderTarget = QWidget(self)
        self.renderTarget.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.renderTarget.setAttribute(Qt.WA_PaintOnScreen)
        self.renderTarget.setMinimumSize(176, 144)
        
        self.timeLine = QSlider(Qt.Horizontal)
        
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        
        layout = QVBoxLayout()
        layout.addWidget(self.controller)
        layout.addWidget(self.renderTarget)
        layout.addWidget(self.timeLine)
        layout.addWidget(self.log)
        self.setLayout(layout)
        
        self.mplayerProcess = QProcess(self)
        
        self.poller = QTimer(self)
        
        self.connect(self.controller, SIGNAL('clicked()'), self.switchPlayState)
        self.connect(self.mplayerProcess, SIGNAL('readyReadStandardOutput()'), self.catchOutput)
        self.connect(self.mplayerProcess, SIGNAL('finished(int, QProcess::ExitStatus)'), self.mplayerEnded) # Les signatures restent les meme en PyQt
        self.connect(self.poller, SIGNAL('timeout()'), self.pollCurrentTime)
        self.connect(self.timeLine, SIGNAL('sliderMoved(int)'), self.timeLineChanged)
    
    
    def closeEvent(self,event):
        self.stopMPlayer()
        event.accept()
    
    def startMPlayer(self):
        if self.isPlaying:
            return True
        
        args = QStringList()
        
        # On demande à utiliser mplayer comme backend
        args << "-slave"
        # Et on veut ne pas avoir trop de chose à parser :)
        args << "-quiet"
        
        # Sous linux, aucun driver n'a été nécessaire et pas de manip pour Wid :)
        if os.name in ['posix', 'mac']:
            args << "-wid" << QString.number(self.renderTarget.winId())
            args << "-vo" << "x11"     # probablement pas indispensable, mais assure que ca marche, normalement. gl est probablement un meilleur choix.
            self.log.append("Video output driver may not be necessary for your platform. \
                        Check: http:#www.mplayerhq.hu/DOCS/man/en/mplayer.1.html \
                        at the VIDEO OUTPUT DRIVERS section.")
        # Sous windows
        elif os.name=='nt':
            args << "-wid" << self.renderTarget.winId().__hex__()
            args << "-vo" << "gl"   # semble mieux fonctionner que "directx:noaccel", mais c'est peut-etre seulement sur ma machine
        
        args << movieFile
        
        # On parse la stdout et stderr au même endroit, donc on demande à "fusionnner" les 2 flux
        self.mplayerProcess.setProcessChannelMode(QProcess.MergedChannels)
        self.mplayerProcess.start(mplayerPath, args)
        if not self.mplayerProcess.waitForStarted(3000):
            qDebug("allez, cherche le bug :o")
            return False
        
        # On récupère les infos de base
        self.mplayerProcess.write("get_video_resolution\n")
        self.mplayerProcess.write("get_time_length\n")
        
        self.poller.start(1000)
        
        self.isPlaying = True
        
        return True
    
    def stopMPlayer(self):
        if self.mplayerProcess.state() == QProcess.NotRunning: ### ajouté pour ne pas avoir de bogue à la fin de la lecture de la vidéo
                return True
        if not self.isPlaying:
            return True
        
        self.mplayerProcess.write("quit\n")
        if not self.mplayerProcess.waitForFinished(3000):
            qDebug("ZOMG, ça plante :(")
            return False
        
        return True
    
    def catchOutput(self):
        while self.mplayerProcess.canReadLine():
            buff=QByteArray(self.mplayerProcess.readLine()) ## 'buffer' est un mot cle python
            self.log.append(QString(buff))
            
            # On vérifie si on a eu des réponses
            # réponse à get_video_resolution : ANS_VIDEO_RESOLUTION='<width> x <height>'
            if buff.startsWith("ANS_VIDEO_RESOLUTION"):
                buff.remove(0, 21) # vire ANS_VIDEO_RESOLUTION=
                buff.replace(QByteArray("'"), QByteArray(""))
                buff.replace(QByteArray(" "), QByteArray(""))
                buff.replace(QByteArray("\n"), QByteArray(""))
                buff.replace(QByteArray("\r"), QByteArray(""))
                # print: informations de déboguage
                #print "-----buff.indexOf('x') :", buff.indexOf('x'), type(buff.indexOf('x'))
                sepIndex = buff.indexOf('x')
                #print "-----buff.left(sepIndex).toInt():", buff.left(sepIndex).toInt(), type(buff.left(sepIndex).toInt())
                resX = buff.left(sepIndex).toInt()[0]
                #print "-----buff.mid(sepIndex+1).toInt() :", buff.mid(sepIndex+1).toInt(), type(buff.mid(sepIndex+1).toInt())
                resY = buff.mid(sepIndex+1).toInt()[0]
                self.renderTarget.setMinimumSize(resX, resY)
            # réponse à get_time_length : ANS_LENGTH=xx.yy
            elif buff.startsWith("ANS_LENGTH"):
                buff.remove(0, 11) # vire ANS_LENGTH=
                buff.replace(QByteArray("'"), QByteArray(""))
                buff.replace(QByteArray(" "), QByteArray(""))
                buff.replace(QByteArray("\n"), QByteArray(""))
                buff.replace(QByteArray("\r"), QByteArray(""))
                #print "-----buff.toFloat() :", buff.toFloat(), type(buff.toFloat())
                maxTime = buff.toFloat()[0]
                self.timeLine.setMaximum(maxTime+1)    ### j'ai viré 'static_cast' car c'est un mot-clé c++
            
            # réponse à get_time_pos : ANS_TIME_POSITION=xx.y
            elif buff.startsWith("ANS_TIME_POSITION"):
                buff.remove(0, 18) # vire ANS_TIME_POSITION=
                buff.replace(QByteArray("'"), QByteArray(""))
                buff.replace(QByteArray(" "), QByteArray(""))
                buff.replace(QByteArray("\n"), QByteArray(""))
                buff.replace(QByteArray("\r"), QByteArray(""))
                #print "-----buff.toFloat() :", buff.toFloat(), type(buff.toFloat())
                currTime = buff.toFloat()[0]
                self.timeLine.setValue(currTime+1)     ### j'ai viré 'static_cast' car c'est un mot-clé c++
    
    def pollCurrentTime(self):
        self.mplayerProcess.write("get_time_pos\n")
    
    # Dirige la timeline
    def timeLineChanged(self, pos):
        self.mplayerProcess.write(QString("seek " + QString.number(pos) + " 2\n").toUtf8())
    
    # Play/stop
    def switchPlayState(self):
        if not self.isPlaying:
            if not self.startMPlayer():
                return
            self.log.clear()
            self.controller.setText(u"Arrêt")
            self.isPlaying = True
        else:
            if not self.stopMPlayer():
                return
            self.poller.stop()
            self.log.clear()
            self.controller.setText("Lecture")
            self.isPlaying = False
    
    def mplayerEnded(self, exitCode, exitStatus):
        self.isPlaying = False
        self.controller.setText("Lecture")
        self.poller.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = PlayerWidget()
    main.show()
    sys.exit(app.exec_()) 
