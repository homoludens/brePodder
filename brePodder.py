from download import *
from sql import DBOperation
#from getfavicon import getIcoUrl

#import vimpdb; vimpdb.set_trace()

#import sys
#sys.setdefaultencoding('utf-8')

feedparser = None
getfavicon = None



draggable = QtCore.Qt.ItemIsDragEnabled
droppable = QtCore.Qt.ItemIsDropEnabled
editable  = QtCore.Qt.ItemIsEditable
enabled   = QtCore.Qt.ItemIsEnabled
selectable = QtCore.Qt.ItemIsSelectable
noflags = QtCore.Qt.NoItemFlags

class updateChannelThread(QtCore.QThread):

    updatesignal2 = QtCore.pyqtSignal()
    updateProgressSignal = QtCore.pyqtSignal()
    updateDoneSignal = QtCore.pyqtSignal()

    def __init__(self,channel, ui,  updateProgress = 0):
        QtCore.QThread.__init__(self)
        self.channel = channel
        self.ui = ui
        self.updateProgress = updateProgress
        self.newEpisodeExists = 0


    def run(self):
        #ui.Mutex.lock()
        self.ui.Sem.acquire(1)
        #TODO: SQL--this one is in thread and is making problems
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        con.isolation_level = None
        cur = con.cursor()

        self.updateChannel(self.channel,  cur)

        con.commit()
        cur.close()

        if self.newEpisodeExists:
            self.updatesignal2.emit()

        self.updateProgressSignal.emit()

        if self.updateProgress == 0:
            self.updateDoneSignal.emit()
        #ui.Mutex.unlock()
        self.ui.Sem.release(1)


    def updateChannel(self, ch = None, cursor=None):

        global feedparser
        if  feedparser is None:
            import feedparser

        newEpisode={}
        cur=cursor
        oldEpisodes=[]
        if ch == None:
            a,  tt = self.ui.db.getCurrentChannel(self.ui.CurrentChannel[1])
#            cc = cur.execute('select id,title from sql_channel where title =?', (self.CurrentChannel,))
#            a = cc.fetchone()#            tt = cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0]))
        else:
#            a,  tt = self.ui.db.getCurrentChannel(ch[1])
            #TODO: SQL--this one is in thread and is making problems
            cc = cur.execute('select id,title,link from sql_channel where title =?', (ch[1],))
            a = cc.fetchone()
            tt = cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0],))

        newEpisode['channel_id'] = a[0]
        epcount=0
        for j in tt:
            oldEpisodes.append(j[1])
            epcount=epcount+1

        feedLink = a[2]
        w = feedparser.parse(feedLink)

        for i in w.entries:
            try:
                aa=oldEpisodes.index(i.title)
            except ValueError:
                aa=None

            if i.has_key('title') and aa==None:
		#print 'epizoda NE postoji'
                self.newEpisodeExists=1
                if i.title:
                    newEpisode['title']=i.title
                else:
                    newEpisode['title']=u'No Title'
                if i.has_key('enclosures'):
                    try:
                        newEpisode['enclosure'] = i.enclosures[0].href
                    except:
                        newEpisode['enclosure'] = "None"

                    try:
                        newEpisode['size'] = int(i.enclosures[0].length)
                    except:
                        newEpisode['size']='1'
                    newEpisode['status'] = u"new"
                else:
                    newEpisode['enclosure'] = u'no file'
                    newEpisode['size'] = '0'
                    newEpisode['status'] = u"none"
                if i.has_key('summary_detail'):
                    newEpisode['description'] = i.summary_detail.value
                else:
                    newEpisode['description'] = u'No description'
                if i.has_key('updated'):
                    if i.updated_parsed:
                        epDate=mktime(i.updated_parsed)
                    else:
                        epDate=mktime(gmtime())
                else:
                    epDate=mktime(gmtime())
                newEpisode['date'] = epDate
                nEpisode=(newEpisode['title'], newEpisode['enclosure'], newEpisode['size'], newEpisode['date'], newEpisode['description'], newEpisode['status'], newEpisode['channel_id'])
                self.ui.db.insertEpisode(nEpisode)
            #cur.execute('insert into sql_episode(title, enclosure, size, date, description, status, channel_id) values (?,?,?,?,?,?,?) ', nEpisode)

            elif not i.has_key('title'):
                print("NEMA NASLOVA EPIZODE")
            else:
                if j[2] != u"old":
                    try:
                        #print "old"
                        self.ui.db.updateEpisodeStatus(j[0])
                    except Exception as ex:
                        print(ex)
                        print(j)
                #cur.execute('update  sql_episode set status= "old" where sql_episode.id = ?',(j[0],) )


class BrePodder(MainUi):
    def memory_usage(a):
        """Memory usage of the current process in kilobytes."""
        status = None
        result = {'peak': 0, 'rss': 0}
        try:
            # This will only work on systems with a /proc file system
            # (like Linux).
            status = open('/proc/self/status')
            for line in status:
                parts = line.split()
                key = parts[0][2:-1].lower()
                if key in result:
                    result[key] = int(parts[1])
        finally:
            if status is not None:
                status.close()
        return result



    def episode_activated(self):
        if self.treeWidget_2.selectedItems():
            selection = self.treeWidget_2.selectedItems()[0]
            try:
                e = self.db.getEpisodeByTitle( selection.text(0) )

                if e.get("enclosure"):
                    enc = e.get("enclosure")
                else:
                    enc = 'None'
                if e.get("description"):
                    desc = e.get("description")
                else:
                    desc='None'
                if e.get("localfile"):
                    localFile = e.get("localfile")
                else:
                    localFile='None'

                self.QTextBrowser1.setHtml("<p>"+desc+"</br>\n\r</p><p><b>FILE: </b><a href="+enc+">"+enc+"</a></p>\
                                            <p><b>LOCALFILE: </b><a href="+localFile+">"+localFile+"</a></p>\
                                            <p>PLAY:<audio  controls='controls' src='"+enc+"'/></p>")


                #~ if (localFile != 'None') & (AudioPlayer):
                    #~ self.AudioPlayer.setUrl(localFile)
                #~ else:
                    #~ self.AudioPlayer.setUrl(enc)
            except e:
                print(e)
                print("EpisodeActivated exception")

    def DownloadActivated(self, a, i):
        self.itemZaPrekid=a
        self.actionCancel.setToolTip("Remove Selected Download")
        self.actionPause.setToolTip("Pause Selected Download")
        self.actionResume.setToolTip("Resume Selected Download")

    def EpisodeDoubleClicked(self, a):
	# TODO: change backgroundColor or something else with QBrush
        a.setFont(0, self.fontBold)
        episodeTitle = a.text(0)
        e = self.db.getEpisodeByTitle( episodeTitle )
        channel = self.db.getChannelById( e.get("channel_id") )
        ChannelDir = self.p.sub("", channel.get("title") )
        #print "ChannelDir: "
	#print ChannelDir

        os.chdir(os.path.expanduser('~')+'/.brePodder/'+ChannelDir)
        item = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item.setText(0, channel.get("title") )
        item.setText(1, e.get("title") )
        item.setText(2, self.getReadableSize( e.get("size") ) )
        item.setText(3, '0')
        item.setText(4, '0')

        try:
            item.setText(5,e.get("enclosure"))
        except TypeError:
            print(TypeError)
            item.setText(5,"No link")


        if len(self.downloadList)>0:
            downloadId = self.downloadList[-1][0] + 1
        else:
            downloadId = 0

        self.itemsDownloading.append( (downloadId, e.get("enclosure").replace(" ", "%20")))
        self.downloadList.append((downloadId, Download( e.get("enclosure").replace(" ", "%20"), item, downloadId, self )))

        os.chdir( os.path.expanduser('~')+'/.brePodder' )

    def AddChannel(self, newUrl = None):

        global feedparser
        if  feedparser is None:
            import feedparser

        global getfavicon
        if getfavicon is None:
            from getfavicon import getIcoUrl


        os.chdir( os.path.expanduser('~')+'/.brePodder' )

        print(newUrl)
        print(self.QLineEdit1.text())
        if not newUrl:
            feedLink = self.QLineEdit1.text()
        else:
            feedLink = newUrl

        print(feedLink)
        w = feedparser.parse(feedLink)
        #item = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item = QtWidgets.QTreeWidgetItem(self.treeWidget)

        if w.feed.has_key('title'):
            ChannelTitle=w.feed.title
        elif w.feed.has_key('link'):
            ChannelTitle=w.feed.link
        else:
            ChannelTitle=feedLink

        ChannelDir = self.p.sub("",ChannelTitle)
        print("ChannelDir: ")
        print(ChannelDir)
        print(os.getcwd())
        try:
            os.mkdir(ChannelDir)
        except:
            print("directory exists")

        os.chdir(ChannelDir)
        item.setText(0,ChannelTitle)

        # download Channel logo
        if w.feed.has_key('image'):
            if w.feed.image.href != None:
                if (w.feed.image.href[0] == '/'):
                    imageURL = w.feed.link +  w.feed.image.href
                else:
                    imageURL = w.feed.image.href

                item.setText(1, imageURL)
                item.setText(5, imageURL)

        if len(self.downloadList)>0:
            downloadId = self.downloadList[-1][0]+1
        else:
            downloadId = 0

        self.itemsDownloading.append( (downloadId, imageURL))
        self.downloadList.append((downloadId, Download( imageURL, item, downloadId, self )))

        url_done = QtCore.QUrl(imageURL)
        fileInfo = QtCore.QFileInfo(url_done.path())
        fileName = fileInfo.fileName()
        #TODO: should we put original or 128px version of logo
        logo_fileBig = ChannelDir+"/"+fileName
            #~ else:
                #~ logo_fileBig=u"images/musicstore2.png"
        #~ else:
            #~ logo_fileBig=u"images/musicstore2.png"

        #  download favicon
        if w.feed.has_key("link"):
            favicon_url = getIcoUrl("http://"+QtCore.QUrl(w.feed.link).host())
        else:
            favicon_url = "http://www.google.com/favicon.ico"

        if favicon_url:
            url = favicon_url
        else:
            url = "http://"+QtCore.QUrl(w.feed.link).host()+"/favicon.ico"

        print("favicon_url:")
        print(favicon_url)


        url_favicon = QtCore.QUrl( url )
        faviconInfo = QtCore.QFileInfo( url_favicon.path() )
        favicon = faviconInfo.fileName()

        logo_file = ChannelDir  + '/' + favicon

        item2 = QtWidgets.QTreeWidgetItem(self.treeWidget)

        if w.feed.has_key('title'):
            item2.setText(0,w.feed.title)
        else:
            item2.setText(0, "No title")

        item2.setText(1,url)
        item2.setText(5,url)

        if len( self.downloadList )>0:
            downloadId = self.downloadList[-1][0] + 1
        else:
            downloadId = 0

        self.itemsDownloading.append( (downloadId, url ))
        self.downloadList.append((downloadId, Download( url, item2, downloadId, self )))

        self.downloadList[downloadId][1].faviconFound=True

        if w.feed.has_key('subtitle'):
            ChannelSubtitle=w.feed.subtitle
        else:
            ChannelSubtitle=u'No description'


        if w.feed.has_key('links'):
            ChannelHomepage = w.feed.links[0].href
#            ChannelHomepage = w.feed.links[1].href
        else:
            ChannelHomepage='http://google.com'

        newChannel = ( ChannelTitle, feedLink, ChannelHomepage,  ChannelSubtitle, logo_file, logo_fileBig )
        self.db.insertChannel( newChannel )

        ChannelId = self.db.getChannelByTitle(ChannelTitle)

        for i in w.entries:

            newEpisode = []

            if i.has_key('title'):
                newEpisode.append(i.title)
            else:
                newEpisode.append(u'pajseri nisu stavili naziv epizode')

            if i.has_key('enclosures'):
                    newEpisode.append(i.enclosures[0].href)
                    try:
                        newEpisode.append(i.enclosures[0].length)
                    except:
                        newEpisode.append( 1 )
            else:
                newEpisode.append("None")
                newEpisode.append(0)

            if i.has_key('updated'):
#                epDate=strftime("%x", i.updated_parsed)
                if i.updated_parsed:
                    epDate=mktime( i.updated_parsed )
            elif i.has_key('published'):
                epDate=mktime( i.published_parsed )
            else:
                epDate=mktime(gmtime())

            newEpisode.append(epDate)

            if i.has_key('summary_detail'):
                newEpisode.append(i.summary_detail.value)
            else:
                newEpisode.append('')

            newEpisode.append('new')
            newEpisode.append(ChannelId[0])

            self.db.insertEpisode( newEpisode )

        self.update_channel_list()
        os.chdir( os.path.expanduser('~') + '/.brePodder' )


    def channel_activated(self):
        #selection = self.listWidget.selectedItems()
        selection =  self.listWidget.currentItem().text(0)
        if selection:
            self.CurrentChannel = selection
        try:
            self.update_episode_list( selection )
        except:
            #if is folder
            pass

#            self.update_episode_list(selection[0].text(0).toUtf8().data().decode('UTF8'))
#            self.CurrentChannel = selection[0].text(0).toUtf8().data().decode('UTF8')
            self.actionCancel.setToolTip("Delete Selected Channel")
            self.actionUpdateFeeds.setToolTip("Update Selected Channel")


    def delete_channel(self):
        if self.tab.isVisible():
            try:
                self.db.deleteAllEpisodes( self.CurrentChannel )
                self.db.deleteChannel( self.CurrentChannel )

                os.chdir(os.path.expanduser('~') + '/.brePodder/')
                ChannelDir = os.path.expanduser('~')+'/.brePodder/' + self.p.sub("", self.CurrentChannel)

                import shutil
                shutil.rmtree(ChannelDir)
            except:
                self.db.deleteTaxonomy( self.CurrentChannel )

        self.update_channel_list()

    # last 50 downloadowed episodes
    def update_lastest_episodes_list(self):
        episodes = self.db.getLatestDownloads()
        self.treeWidget_4.clear()

        #self.AudioPlayer_latestDownloads.setUrl( episodes[0][3] )

        for e in episodes:
            item = QtWidgets.QTreeWidgetItem( self.treeWidget_4 )
            item.setText( 0, str(e[10]) )
            item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~') + '/.brePodder/' + e[14])))
            item.setText( 1, e[1] )
            item.setText( 2, self.getReadableSize(e[4]) )
            item.setText( 3, os.path.expanduser('~') + '/.brePodder/' + str(e[3]) )

    # newest episodes
    def update_newest_episodes_list(self):
        episodes = self.db.getLatestEpisodes()
        self.treeWidget_5.clear()

	#self.AudioPlayer_newestEpisodes.setUrl( episodes[0][2] )

        for e in episodes:
            item = QtWidgets.QTreeWidgetItem( self.treeWidget_5 )
            item.setText( 0, e[10] )
            item.setIcon( 0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~') + '/.brePodder/' + e[14])) )
            item.setText( 1, e[1] )
            if e[4]:
                item.setText(2,self.getReadableSize( e[4]) )
            else:
                item.setText(2,'???')
            try:
                b=gmtime(float(e[5]))
                epDate=strftime("%x", b)
            except:
                b=gmtime()
                epDate=strftime("%x", b)

            item.setText(3, epDate)

            if ( e[2] and  e[2] != 'None' ):
                item.setText(4, e[2])



    #TODO: Send file to some media player
    def LastestEpisodeDoubleClicked(self, a):
        #os.system( "mocp -a " + a.text(3).toUtf8().data().decode('UTF8') )
        self.AudioPlayer_latestDownloads.setUrl( a.text(3) )
        self.AudioPlayer_latestDownloads.playClicked()

    def LastestEpisodeActivated(self, a):
        #os.system( "mocp -a " + a.text(3).toUtf8().data().decode('UTF8') )
        #self.AudioPlayer_latestDownloads.setUrl( a.text(3).toUtf8().data().decode('UTF8') )
        pass

    def NewestEpisodeDoubleClicked( self, a):
        #print  a.text(4).toUtf8().data().decode('UTF8')
        episode = a.text(4)
        #print episode.get("enclosure")
        print(episode + " added to queue")
        self.AudioPlayer_newestEpisodes.setUrl( episode )

    def getReadableSize(self,  size):
        if size:
            if (size) > 1024*1024:
                try:
                    sizeReadable = str(size/1024/1024)+' MB'
                except:
                    sizeReadable = size
            elif (size) > 1024:
                sizeReadable = str(size/1024)+' kB'
            else:
                sizeReadable = str(size)+' B'
        else:
            sizeReadable = 'None'
        return sizeReadable

    def update_episode_list(self,channel_Title):
        cc = self.db.getChannelByTitle(channel_Title)
#        self.QTextBrowser1.setHtml("<p><img src="+"'"+cc.logobig+"'"+"><br>\n\n</p><p>"+cc.description+"</p><p><b>Homepage: </b><a href="+cc.homepage+">"+cc.homepage+"</a><p>")
#        self.QTextBrowser1.setHtml("<p>"+cc.description+"</p><p><b>Homepage: </b><a href="+cc.homepage+">"+cc.homepage+"</a></p>")
        self.QTextBrowser1.setHtml("<p>" +cc[4] + "</p>     <p> <b>Feed link:</b> <a href=" + cc[2] + ">" + cc[2]  +  "</a></p> <p><b>Homepage: </b><a href=" + cc[3] + ">" + cc[3] + "</a></p>")

        tt = self.db.getChannelEpisodes(channel_Title)
        self.treeWidget_2.clear()
        for t in tt:
            item2 = QtWidgets.QTreeWidgetItem(self.treeWidget_2)

            if not t[3]:#.localfile:
                item2.setIcon(0,QtGui.QIcon(":/icons/build.png"))
            else:
                item2.setIcon(0,QtGui.QIcon(":/icons/mp3.png"))
            item2.setText(0,t[1]) #.title
            item2.setText(1, self.getReadableSize(t[4])) #.size
            try:
                b=gmtime(float(t[5]))#.date
                epDate=strftime("%x", b)
            except:
                b=gmtime()
                epDate=strftime("%x", b)
                print("date exception")
            item2.setText(2,epDate)

            if t[7] == 'new':
                item2.setFont(0, self.fontBold)

    def update_channel_list(self):
        channels =  self.db.getAllChannelsWOFolder()
        folders = self.db.getAllFolders()

        self.listWidget.clear()

        for folder in folders:
            itemF = QtWidgets.QTreeWidgetItem(self.listWidget)
            itemF.setText(0, folder[1])
            itemF.setIcon(0, QtGui.QIcon(':/icons/folder-blue.png'))
            itemF.setFlags(enabled|droppable)
#            cur.execute('select * from sql_channel where folder_id = ?',(folder[0],))
#            childChannels = cur.fetchall()
            childChannels = self.db.getFolderChannels(folder[0])

            for childChannel in childChannels:
                itemChildChannel = QtWidgets.QTreeWidgetItem(itemF)
                itemChildChannel.setText(0, childChannel[1])
		#print "Ch. icon: "
		#print os.path.expanduser('~') + '/.brePodder/' + childChannel[5]
                itemChildChannel.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~')+'/.brePodder/'+childChannel[5])))
                itemF.addChild(itemChildChannel)

        for channel in channels:
            item = QtWidgets.QTreeWidgetItem(self.listWidget)
#            if channel.episode[-1].status == u'new':
#                item.setFont(0, self.fontBold)
            item.setText(0, channel[1])
	    #print os.path.expanduser('~') + '/.brePodder/' + channel[5]
            item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~')+'/.brePodder/'+channel[5])))
#            item.setToolTip(0,"<p><img src="+"'"+channel.logobig+"'"+"></p><p style='font-size:20pt'><b>"+channel.title+"</b></p><a href="+channel.link+">"+channel.link+"</a>")
            item.setFlags(enabled|draggable|selectable)
# dodati bold za channel koji ima novu epizodu. mislim da je to najefikasnije preko novog polja u bazi.

#        self.cur.close()

    def updateProgressBarFromThread(self):
        self.updateProgressBar.setValue(self.updateProgressBar.value()+1)
        if self.updateProgressBar.value() == self.numberOfChannels-1:
            self.update_done()

    def create_new_foder(self):
        text, ok = QtWidgets.QInputDialog.getText(self.MW, 'Input Dialog', 'Enter name for new folder:')

#        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
#        con.isolation_level = None
#        cur = con.cursor()

        if ok:
#            con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
#            con.isolation_level = None
#            cur2 = con.cursor()
#            cur2.execute('insert into sql_taxonomy(title) values (?)', (text.toUtf8().data(),))
            self.db.insertFolder(text)
        self.update_channel_list()


    def update_channel(self):
        self.QLineEdit1.hide()
        self.QPushButton1.hide()
        self.updateProgressBar.setRange(0,0)
        self.updateProgressBar.show()
        self.numberOfChannels = 1

#        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
#        con.isolation_level = None
#        cur = con.cursor()
#        cur.execute('select * from sql_channel where title = ?',(self.CurrentChannel,))
#        ch = cur.fetchone()

#        ch=Channel.query.filter_by(title=self.CurrentChannel).one()

        ch = self.db.getChannelByTitle(self.CurrentChannel)
#        print "updateChannelThread"
#        print ch

        self.ChannelForUpdate=ch
#        print ch.title
#        ui.Sem.acquire()
        updtChTr=updateChannelThread(ch, self,  0)
        #QtCore.QObject.connect(updtChTr,QtCore.SIGNAL("updatesignal"),self.update_channel_list,QtCore.Qt.QueuedConnection)
        pdtChTr.updatesignal.connect(self.update_channel_list, QtCore.Qt.QueuedConnection)
        #QtCore.QObject.connect(updtChTr,QtCore.SIGNAL("updatesignal_episodelist(PyQt_PyObject)"),self.update_episode_list,QtCore.Qt.QueuedConnection)
        updtChTr.updatesignal_episodelist.connect(self.update_episode_list, QtCore.Qt.QueuedConnection)
        #QtCore.QObject.connect(updtChTr,QtCore.SIGNAL("updateDoneSignal"),self.update_done, QtCore.Qt.BlockingQueuedConnection)
        updtChTr.updateDoneSignal.connect(self.update_done, QtCore.Qt.BlockingQueuedConnection)
        self.ttthread=updtChTr
        updtChTr.start()



    def update_all_channels(self):
        self.QLineEdit1.hide()
        self.QPushButton1.hide()

        self.updateProgressBar.show()

        updtChTr=[]
#        allChannels=Channel.query.all()

#        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
#        con.isolation_level = None
#        cur = con.cursor()
#        cur.execute('select * from sql_channel')
#        allChannels = cur.fetchall()

        allChannels = self.db.getAllChannels()


        self.numberOfChannels = allChannels.__len__()-1
        self.updateProgressBar.setRange(0,self.numberOfChannels+1)
        self.updateProgressBar.setValue(0)
        self.updateProgressBar.setFormat("%v" + " of " + "%m")
        j=0
        for i in allChannels:
            updtChTr.append(updateChannelThread(i, self, j))
            self.TTThread.append(updtChTr[j])
            #QtCore.QObject.connect(updtChTr[j],QtCore.SIGNAL("updateProgressSignal"),self.updateProgressBarFromThread,QtCore.Qt.BlockingQueuedConnection)
            updtChTr[j].updateProgressSignal.connect(self.updateProgressBarFromThread, QtCore.Qt.BlockingQueuedConnection)
            updtChTr[j].start()
            j=j+1

    def sendMessage(self, message):
        try:
            print(message)
            #import pynotify
            #if pynotify.init("brePodder"):
            #    n = pynotify.Notification("brePodder", message)
#                n = pynotify.Notification("Title", "message", "icon-name")
            #    n.show()
            #else:
            #    print "there was a problem initializing the pynotify module"
        except:
            print("you don't seem to have pynotify installed")

    def update_done(self):
            self.updateProgressBar.hide()
            self.QLineEdit1.show()
            self.QPushButton1.show()
            self.update_channel_list()
            self.sendMessage("Updating Done")

