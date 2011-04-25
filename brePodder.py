from Download import *
from sql import DBOperation

class updateChannelThread(QtCore.QThread):
    def __init__(self,channel, ui,  updateProgress = 0):
        QtCore.QThread.__init__(self)
        self.channel = channel
        self.ui = ui
        self.updateProgress = updateProgress
        self.newEpisodeExists = 0
       
    def run(self):
#        ui.Mutex.lock()
        self.ui.Sem.acquire(1)
        
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        con.isolation_level = None
        cur = con.cursor()
        
        self.updateChannel(self.channel,  cur)
       
        con.commit()
        cur.close()
        
        if self.newEpisodeExists:
            self.emit(QtCore.SIGNAL("updatesignal2"))

        self.emit(QtCore.SIGNAL("updateProgressSignal"))
        
        if self.updateProgress == 0:
            self.emit(QtCore.SIGNAL("updateDoneSignal"))
#        ui.Mutex.unlock()
        self.ui.Sem.release(1)
        

    def updateChannel(self, ch = None, cursor=None):
        newEpisode={}
        cur=cursor
        oldEpisodes=[]
#        print "updateChannel: "
#        print ch[1]
        if ch == None:
#            print self.ui.CurrentChannel
            a,  tt = self.ui.db.getCurrentChannel(self.ui.CurrentChannel[1])
#            cc = cur.execute('select id,title from sql_channel where title =?', (self.CurrentChannel,))
#            a = cc.fetchone()
#            tt = cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0]))
        else:
#            a,  tt = self.ui.db.getCurrentChannel(ch[1])
            #TODO: SQL!!!
            cc = cur.execute('select id,title,link from sql_channel where title =?', (ch[1],))
            a = cc.fetchone()
            tt = cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0],))
            
        newEpisode['channel_id'] = a[0]    
#        print a[1]
        epcount=0
        for j in tt:
            oldEpisodes.append(j[1])
            epcount=epcount+1
        feedLink = a[2].decode()
        w = feedparser.parse(feedLink)
        for i in w.entries:
            try:
                aa=oldEpisodes.index(i.title)
            except ValueError:
                aa=None
            
            if i.has_key('title') and aa==None:
#                print 'epizoda NE postoji'
                self.newEpisodeExists=1
                if i.title:
                    newEpisode['title']=i.title
                else:
                    newEpisode['title']=u'No Title'
                if i.has_key('enclosures'):
                    newEpisode['enclosure'] = i.enclosures[0].href
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
#                cur.execute('insert into sql_episode(title, enclosure, size, date, description, status, channel_id) values (?,?,?,?,?,?,?) ', nEpisode)
                
            elif not i.has_key('title'):
                print "NEMA NASLOVA EPIZODE"
            else:
                if j[2]!=u"old":
                    self.ui.db.updateEpisodeStatus(j[0])
#                    cur.execute('update  sql_episode set status= "old" where sql_episode.id = ?',(j[0],) )


class BrePodder(MainUi):
#    def __init__(self):
#        self.db = DBOperation()
#        self.Sem = QtCore.QSemaphore(5)

        
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
                
# TODO: download images from episode description so i can show them in QTextBrowser
# this is beta... :)
    def getImageFromDesc(self, desc,  channel):
#        p=re.compile("\W")  
        ChannelDir = self.p.sub("",channel.title)
        os.chdir(os.path.expanduser('~')+'/.brePodder/'+ChannelDir)
        
        match_obj = self.compile_obj.findall(desc)
        
        for image in match_obj:
            p = re.compile(image)
            i=image.rfind('/')
            desc = p.sub( os.getcwd()+image[i:], desc)
            
            if len(self.downloadList)>0:
                downloadId = self.downloadList[-1][0]+1
            else:
                downloadId = 0
#            print "downloadId: " + str(downloadId)
            self.downloadList.append((downloadId, Download()))
            self.downloadList[downloadId][1].setup(self)
            
            item = QtGui.QTreeWidgetItem(self.treeWidget)
            item.setText(0,channel.title)
            item.setText(5,image)
            
            self.downloadList[downloadId][1].downloadFile(image.replace(" ", "%20"), item, downloadId)
            
        os.chdir(os.path.expanduser('~')+'/.brePodder')            
        return desc
        
    def episode_activated(self):
        if self.treeWidget_2.selectedItems():
            selection = self.treeWidget_2.selectedItems()[0]
            try:
                #TODO: SQL
                e=Episode.query.filter_by(title=selection.text(0).toUtf8().data().decode()).one()
                if e.enclosure:
                    enc=e.enclosure
                else:
                    enc='None'
                if e.description:
                    desc=e.description
                else:
                    desc='None'
                if e.localfile:
                    localFile=e.localfile
                else:
                    localFile='None'
    # TODO: download images from episode description so i can show them in QTextBrowser
    #            desc_localimg = self.getImageFromDesc(desc, e.channel)
    #            print desc_localimg

                self.QTextBrowser1.setHtml("<p>"+desc+"</br>\n\r</p><p><b>FILE: </b><a href="+enc+">"+enc+"</a></p>\
                                            <p><b>LOCALFILE: </b><a href="+localFile+">"+localFile+"</a></p>\
                                            <p>PLAY:<audio_off  controls='controls' src='"+enc+"'/></p>")

            except:
                print "EpisodeActivated exception"
    
    def DownloadActivated(self, a, i):
        self.itemZaPrekid=a
        self.actionCancel.setToolTip("Remove Selected Download")
        self.actionPause.setToolTip("Pause Selected Download")
        self.actionResume.setToolTip("Resume Selected Download")
    
    def EpisodeDoubleClicked(self, a):
# TODO: change backgroundColor or something else with QBrush
        a.setFont(0, self.fontBold) 
        #TODO: SQL  
        e=Episode.query.filter_by(title=a.text(0).toUtf8().data().decode('UTF8')).one()
#        p=re.compile("\W")  
        ChannelDir = self.p.sub("",e.channel.title)
        
        os.chdir(os.path.expanduser('~')+'/.brePodder/'+ChannelDir)
        item = QtGui.QTreeWidgetItem(self.treeWidget)
        item.setText(0,e.channel.title)
        item.setText(1,e.title)
        item.setText(2,self.getReadableSize(e.size))
        item.setText(3,'0')
        item.setText(4,'0')

        try:
            item.setText(5,e.enclosure)
        except TypeError:
            print TypeError
            item.setText(5,"No link")
        
        session.commit()
        
        if len(self.downloadList)>0:
            downloadId = self.downloadList[-1][0]+1
        else:
            downloadId = 0
#        print "downloadId: " + str(downloadId)
        self.itemsDownloading.append((downloadId, e.enclosure.replace(" ", "%20"))) 
        self.downloadList.append((downloadId, Download()))
        self.downloadList[downloadId][1].setup(self)
        self.downloadList[downloadId][1].downloadFile(e.enclosure.replace(" ", "%20"), item, downloadId)
 
          
        os.chdir(os.path.expanduser('~')+'/.brePodder') 

    def AddChannel(self, newUrl = None):
        import feedparser
        if newUrl == None:
            feedLink = self.QLineEdit1.text().toUtf8().data()
        else:
            feedLink = newUrl
        w = feedparser.parse(feedLink)
        item = QtGui.QTreeWidgetItem(self.treeWidget)
        if w.feed.has_key('title'):
            ChannelTitle=w.feed.title
        elif w.feed.has_key('link'):
            ChannelTitle=w.feed.link
        else:
            ChannelTitle=feedLink
            
#        p=re.compile("\W")  
        ChannelDir = self.p.sub("",ChannelTitle)
        try:
            os.mkdir(ChannelDir)
        except:
            print "directory exists"
        os.chdir(ChannelDir)
#        os.makedirs(ChannelTitle.decode())
#        os.chdir(ChannelTitle)

#        logo_file=ChannelTitle + '/favicon.png' 
        item.setText(0,ChannelTitle)
# download Channel logo
        if w.feed.has_key('image'):
            if w.feed.image.href != None:
#            item = QtGui.QTreeWidgetItem(self.treeWidget)
#            item.setText(0,w.feed.title)
                item.setText(1,w.feed.image.href)
                item.setText(5,w.feed.image.href)
 
 
                 
                
                if len(self.downloadList)>0:
                    downloadId = self.downloadList[-1][0]+1
                else:
                    downloadId = 0
#                print "downloadId: " + str(downloadId)
                self.itemsDownloading.append((downloadId, w.feed.image.href))
                self.downloadList.append((downloadId, Download()))
                self.downloadList[downloadId][1].setup(self)
                self.downloadList[downloadId][1].downloadFile(w.feed.image.href, item, downloadId)


                url_done = QtCore.QUrl(w.feed.image.href)
                fileInfo = QtCore.QFileInfo(url_done.path())
                fileName = QtCore.QString(fileInfo.fileName())
                
    #            i = w.feed.image.href.rfind('/')
    #            logo_fileBig = ChannelTitle+"/"+w.feed.image.href[i+1:]

    # should we put original or 128px version of logo
                logo_fileBig = ChannelDir+"/"+fileName.toUtf8().data()
            else: logo_fileBig=u"images/musicstore2.png"
        else: logo_fileBig=u"images/musicstore2.png"
#  download favicon
        from getfavicon import getIcoUrl
        favicon_url=getIcoUrl("http://"+QtCore.QUrl(w.feed.link).host().toUtf8().data())
        if favicon_url:
            url = favicon_url
        else:
            url = "http://"+QtCore.QUrl(w.feed.link).host().toUtf8().data()+"/favicon.ico"
        
        
        url_favicon = QtCore.QUrl(url)
        faviconInfo = QtCore.QFileInfo(url_favicon.path())
        favicon = QtCore.QString(faviconInfo.fileName()).toUtf8().data()
        
#        ifavicon=url.rfind('/')
#        favicon=url[ifavicon+1:]
        logo_file=ChannelDir +'/'+favicon
#        if '.ico' in logo_file :
#            logo_file = logo_file.replace('.ico','.icon')
        item2 = QtGui.QTreeWidgetItem(self.treeWidget)
        item2.setText(0,w.feed.title)
        item2.setText(1,url)
        item2.setText(5,url)
        
        if len(self.downloadList)>0:
            downloadId = self.downloadList[-1][0]+1
        else:
            downloadId = 0
        self.itemsDownloading.append((downloadId, url))
        self.downloadList.append((downloadId, Download()))
        self.downloadList[downloadId][1].setup(self)
        self.downloadList[downloadId][1].faviconFound=True
        self.downloadList[downloadId][1].downloadFile(url, item2, downloadId)
        
        
        if w.feed.has_key('subtitle'):
            ChannelSubtitle=w.feed.subtitle
        else:
            ChannelSubtitle=u'Nema opisa'
#        convert logo_file png:logo_file
#        p = QPixmap(logo_file)
#        im=p.convertToImage()
##            im=im.smoothScale(50,50,QImage.ScaleMin)
#        p.convertFromImage(im)
#        p.save(logo_file,'PNG')
#        os.makedirs(w.feed.title)

        if w.feed.has_key('links'): 
            ChannelHomepage = w.feed.links[0].href
#            ChannelHomepage = w.feed.links[1].href
        else:
            ChannelHomepage='http://google.com'

#        newChannel = Channel(title=ChannelTitle,link=feedLink,description=ChannelSubtitle,logo=logo_file, logobig=logo_fileBig)
        newChannel = Channel(title=ChannelTitle,link=feedLink,description=ChannelSubtitle,logo=logo_file, logobig=logo_fileBig,homepage=ChannelHomepage)
        for i in w.entries:
            if i.has_key('title'):
                newEpisode = Episode(title=i.title)
            else:
                newEpisode = Episode(title=u'pajseri nisu stavili naziv epizode')
            if i.has_key('enclosures'):
                newEpisode.enclosure = i.enclosures[0].href
                try:
                    newEpisode.size = i.enclosures[0].length
                except:
                    newEpisode.size = 1
            if i.has_key('summary_detail'):
                newEpisode.description = i.summary_detail.value
            if i.has_key('updated'):
#                epDate=strftime("%x", i.updated_parsed)
                if i.updated_parsed:
                    epDate=mktime(i.updated_parsed)
                    newEpisode.date = epDate
                else:
                    epDate=mktime(gmtime())

            newChannel.episode.append(newEpisode)
        session.commit()
        self.update_channel_list()
        os.chdir(os.path.expanduser('~')+'/.brePodder') 
        

    def channel_activated(self):
        selection = self.listWidget.selectedItems()
        if selection:
            self.update_episode_list(selection[0].text(0).toUtf8().data().decode('UTF8'))
            self.CurrentChannel = selection[0].text(0).toUtf8().data().decode('UTF8')
            self.actionCancel.setToolTip("Delete Selected Channel")
            self.actionUpdateFeeds.setToolTip("Update Selected Channel")
        
    
    def delete_channel(self):
        if self.tab.isVisible():
            self.db.deleteAllEpisodes(self.CurrentChannel)
            self.db.deleteChannel(self.CurrentChannel)

            os.chdir(os.path.expanduser('~')+'/.brePodder/')
            ChannelDir = os.path.expanduser('~')+'/.brePodder/'+self.p.sub("", self.CurrentChannel)
            
            import shutil
            shutil.rmtree(ChannelDir)
#            session.commit()
            self.update_channel_list()

#last 20 downloadowed episodes
    def update_lastest_episodes_list(self):

#        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
#        con.isolation_level = None
#        cur = con.cursor()
#        cur.execute('SELECT * FROM sql_episode WHERE status="downloaded" ORDER BY date DESC LIMIT 50')
#        episodes = cur.fetchall()

        episodes = self.db.getLatestDownloads()
        self.treeWidget_4.clear()

        #episodes=Episode.query.filter_by(status=u'downloaded').order_by(Episode.id.desc()).limit(50).all()
        for e in episodes:
            item = QtGui.QTreeWidgetItem(self.treeWidget_4)
            item.setText(0,str(e[8]))
            item.setText(1,e[1])
            item.setText(2,self.getReadableSize(e[4]))
            item.setText(3,os.path.expanduser('~')+'/.brePodder/'+str(e[3]))
            
#newest episodes
    def update_newest_episodes_list(self):
#        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
#        con.isolation_level = None
#        cur = con.cursor()
#        cur.execute('SELECT * FROM sql_episode EP, sql_channel CH WHERE EP.channel_id = CH.id ORDER BY date DESC LIMIT 50')
#        episodes = cur.fetchall()
        
#        episodes=Episode.query.order_by(Episode.date.desc()).limit(40).all()

        episodes = self.db.getLatestEpisodes()
        self.treeWidget_5.clear()
        for e in episodes:
            item = QtGui.QTreeWidgetItem(self.treeWidget_5)
            item.setText(0,str(e[10]))
            item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~')+'/.brePodder/'+e[14])))
            item.setText(1,e[1])
            if e[4]:
                item.setText(2,self.getReadableSize(e[4]))
            else:
                item.setText(2,'???')
            try:
                b=gmtime(float(e[5]))
                epDate=strftime("%x", b)
            except:
                b=gmtime()
                epDate=strftime("%x", b)
            item.setText(3,epDate)
    
    def LastestEpisodeDoubleClicked(self, a):
#        print  a.text(3).toUtf8().data().decode('UTF8')
        os.system("mplayer "+a.text(3).toUtf8().data().decode('UTF8'))
        
    def getReadableSize(self,  size):
        if size:
            if (size) > 1024*1024:
                sizeReadable = str(size/1024/1024)+' MB'
            elif (size) > 1024:
                sizeReadable = str(size/1024)+' kB'
            else:   
                sizeReadable = str(size)+' B'
        else:
            sizeReadable = 'None'
        return sizeReadable
    
    def update_episode_list(self,channel_Title):
#        cc = Channel.query.filter_by(title=channel_Title.toUtf8().data()).one()
#        cc = Channel.query.filter_by(title=channel_Title).one()
        
#        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = True)
#        con.isolation_level = None
#        cur = con.cursor()       
#        cur.execute('select * from sql_channel where title = ?',(channel_Title,))
#        cc = cur.fetchone()

        cc = self.db.getChannelByTitle(channel_Title)
        print cc
#        self.QTextBrowser1.setHtml("<p><img src="+"'"+cc.logobig+"'"+"><br>\n\n</p><p>"+cc.description+"</p><p><b>Homepage: </b><a href="+cc.homepage+">"+cc.homepage+"</a><p>")
#        self.QTextBrowser1.setHtml("<p>"+cc.description+"</p><p><b>Homepage: </b><a href="+cc.homepage+">"+cc.homepage+"</a></p>")
        self.QTextBrowser1.setHtml("<p>"+cc[4]+"</p><p><b>Homepage: </b><a href="+cc[3]+">"+cc[3]+"</a></p>")

        #TODO: SQL
        tt = Episode.query.filter(Episode.channel.has(title=channel_Title)).order_by(Episode.date.desc()).all() 
        self.treeWidget_2.clear()
        for t in tt:
            item2 = QtGui.QTreeWidgetItem(self.treeWidget_2)
            if not t.localfile:
                item2.setIcon(0,QtGui.QIcon("images/build.png"))
            else:
                item2.setIcon(0,QtGui.QIcon("images/mp3.png"))
            item2.setText(0,t.title)
            item2.setText(1,self.getReadableSize(t.size))
            try:
                b=gmtime(float(t.date))
                epDate=strftime("%x", b)
            except:
                b=gmtime()
                epDate=strftime("%x", b)
                print "date exception"
            item2.setText(2,epDate)
#            if t.status=='new':
#                item2.setFont(0, self.fontBold)
         
    def update_channel_list(self):
        
#        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
#        con.isolation_level = None
#        cur = con.cursor()
        
#        cur.execute('select * from sql_channel where folder_id IS NULL')
#        channels = cur.fetchall()
#        
#        cur.execute('select * from sql_taxonomy')
#        folders = cur.fetchall()
        
#        channels = Channel.query.all()
#        folders = Taxonomy.query.all()
        channels =  self.db.getAllChannelsWOFolder()
        folders = self.db.getAllFolders()

        
        self.listWidget.clear()
        
        for folder in folders:
            itemF = QtGui.QTreeWidgetItem(self.listWidget)
            itemF.setText(0, folder[1])
            itemF.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~')+'/.brePodder/images/directory.png')))
            itemF.setFlags(enabled|droppable)      
#            cur.execute('select * from sql_channel where folder_id = ?',(folder[0],))
#            childChannels = cur.fetchall()
            childChannels = self.db.getFolderChannels(folder[0])
            
            for childChannel in childChannels:
                itemChildChannel = QtGui.QTreeWidgetItem(itemF)
                itemChildChannel.setText(0, childChannel[1])
                itemChildChannel.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~')+'/.brePodder/'+childChannel[5])))
                itemF.addChild(itemChildChannel)
            
        for channel in channels:
            item = QtGui.QTreeWidgetItem(self.listWidget)
#            if channel.episode[-1].status == u'new':
#                item.setFont(0, self.fontBold)
            item.setText(0, channel[1])
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
        text, ok = QtGui.QInputDialog.getText(self.MW, 'Input Dialog', 'Enter name for new folder:')
        
#        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
#        con.isolation_level = None
#        cur = con.cursor()

        if ok:
#            con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
#            con.isolation_level = None
#            cur2 = con.cursor()
#            cur2.execute('insert into sql_taxonomy(title) values (?)', (text.toUtf8().data(),))
            self.db.insertFolder(text.toUtf8().data())
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
        updtChTr=updateChannelThread(ch,self,  0)
        QtCore.QObject.connect(updtChTr,QtCore.SIGNAL("updatesignal"),self.update_channel_list,QtCore.Qt.QueuedConnection)
        QtCore.QObject.connect(updtChTr,QtCore.SIGNAL("updatesignal_episodelist(PyQt_PyObject)"),self.update_episode_list,QtCore.Qt.QueuedConnection)
        QtCore.QObject.connect(updtChTr,QtCore.SIGNAL("updateDoneSignal"),self.update_done, QtCore.Qt.BlockingQueuedConnection)
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
        self.updateProgressBar.setFormat(QtCore.QString("%v" + " of " + "%m"))
        j=0
        for i in allChannels:   
            updtChTr.append(updateChannelThread(i, self, j))
            self.TTThread.append(updtChTr[j])
            QtCore.QObject.connect(updtChTr[j],QtCore.SIGNAL("updateProgressSignal"),self.updateProgressBarFromThread,QtCore.Qt.BlockingQueuedConnection)
            updtChTr[j].start()
            j=j+1
    
    def sendMessage(self, message):
        try:
            import pynotify
            if pynotify.init("brePodder"):
                n = pynotify.Notification("brePodder", message)
#                n = pynotify.Notification("Title", "message", "icon-name")
                n.show()
            else:
                print "there was a problem initializing the pynotify module"
        except:
            print "you don't seem to have pynotify installed"        

    def update_done(self):
            self.updateProgressBar.hide()
            self.QLineEdit1.show()
            self.QPushButton1.show()
            self.update_channel_list()
            self.sendMessage("Updating Done")

