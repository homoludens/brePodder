from io import BytesIO

from PyQt5 import QtCore, QtWidgets, QtGui
from time import gmtime, strftime, mktime
from utils.download import *
from utils.get_favicon import get_icon_url, get_icon, download_image
import feedparser
import requests
import os
import sqlite3
from ui.Ui_mainwindow import MainUi
from utils.youtube import is_video_link, is_channel_url, get_youtube_rss, get_channel_url

import logging


draggable = QtCore.Qt.ItemIsDragEnabled
droppable = QtCore.Qt.ItemIsDropEnabled
editable = QtCore.Qt.ItemIsEditable
enabled = QtCore.Qt.ItemIsEnabled
selectable = QtCore.Qt.ItemIsSelectable
noflags = QtCore.Qt.NoItemFlags


class UpdateChannelThread(QtCore.QThread):
    updatesignal = QtCore.pyqtSignal()
    updateProgressSignal = QtCore.pyqtSignal()
    updateDoneSignal = QtCore.pyqtSignal()
    updatesignal_episodelist = QtCore.pyqtSignal()

    def __init__(self, channel, ui, update_progress=0):
        QtCore.QThread.__init__(self)
        self.channel = channel
        self.ui = ui
        self.updateProgress = update_progress
        self.newEpisodeExists = 0
        self.main_directory = os.path.expanduser('~') + '/.brePodder/'

    def run(self):
        # ui.Mutex.lock()
        self.ui.Sem.acquire(1)
        # TODO: SQL--this one is in thread and is making problems
        con = sqlite3.connect(self.main_directory + "podcasts.sqlite", check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()

        self.update_channel(self.channel, cur)

        con.commit()
        cur.close()

        if self.newEpisodeExists:
            self.updatesignal.emit()

        self.updateProgressSignal.emit()

        if self.updateProgress == 0:
            self.updateDoneSignal.emit()
        # ui.Mutex.unlock()
        self.ui.Sem.release(1)

    def update_channel(self, ch=None, cursor=None):

        new_episode = {}
        cur = cursor
        old_episodes = []
        if ch is None:
            a, tt = self.ui.db.getCurrentChannel(self.ui.CurrentChannel[1])
        #            cc = cur.execute('select id,title from sql_channel where title =?', (self.CurrentChannel,))
        #            a = cc.fetchone()
        #            tt = cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0]))
        else:
            #            a,  tt = self.ui.db.getCurrentChannel(ch[1])
            # TODO: SQL--this one is in thread and is making problems
            cc = cur.execute('select id,title,link from sql_channel where title =?', (ch[1],))
            a = cc.fetchone()
            tt = cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0],))

        new_episode['channel_id'] = a[0]
        epcount = 0
        for j in tt:
            old_episodes.append(j[1])
            epcount = epcount + 1

        feed_link = a[2]

        # Do request using requests library and timeout
        content = ''
        try:
            resp = requests.get(feed_link, timeout=10.0, headers=self.headers)
        except requests.ReadTimeout as e:
            # logger.warn("Timeout when reading RSS %s", rss_feed)
            print('timeout', e)
            return
        except requests.exceptions.ConnectionError as e:
            print('404', e)
            return ''
        except requests.exceptions.HTTPError as e:
            print('404', e)
            return ''
        except requests.exceptions.MissingSchema as e:
            print('MissingSchema', e)
        else:
            content = BytesIO(resp.content)

        feed = feedparser.parse(content)

        for i in feed.entries:
            try:
                aa = old_episodes.index(i.title)
            except ValueError:
                aa = None

            if 'title' in i and aa is None:
                # print 'epizoda NE postoji'
                self.newEpisodeExists = 1
                if i.title:
                    new_episode['title'] = i.title
                else:
                    new_episode['title'] = u'No Title'
                if 'enclosures' in i:
                    try:
                        new_episode['enclosure'] = i.enclosures[0].href
                    except:
                        print("catch all excetions brePodder.py 125")
                        new_episode['enclosure'] = "None"

                    try:
                        new_episode['size'] = int(i.enclosures[0].length)
                    except:
                        print("catch all excetions brePodder.py 131")
                        new_episode['size'] = '1'
                    new_episode['status'] = u"new"
                else:
                    new_episode['enclosure'] = u'no file'
                    new_episode['size'] = '0'
                    new_episode['status'] = u"none"
                if 'summary_detail' in i:
                    new_episode['description'] = i.summary_detail.value
                else:
                    new_episode['description'] = u'No description'

                episode_date = mktime(gmtime())
                if 'updated' in i:
                    if i.updated_parsed:
                        episode_date = mktime(i.updated_parsed)
                elif 'published' in i:
                    episode_date = mktime(i.published_parsed)

                new_episode['date'] = episode_date
                new_episode_tupple = (new_episode['title'], new_episode['enclosure'], new_episode['size'],
                                      new_episode['date'], new_episode['description'], new_episode['status'],
                                      new_episode['channel_id'])
                self.ui.db.insertEpisode(new_episode_tupple)

            elif 'title' not in i:
                print("No title")
            else:
                if j[2] != u"old":
                    try:
                        # print "old"
                        self.ui.db.updateEpisodeStatus(j[0])
                    except Exception as ex:
                        print(ex)
                        print(j)
                # cur.execute('update  sql_episode set status= "old" where sql_episode.id = ?',(j[0],) )


class AddChannelThread(QtCore.QThread):
    addsignal = QtCore.pyqtSignal()
    addProgressSignal = QtCore.pyqtSignal()
    addDoneSignal = QtCore.pyqtSignal()
    addsignal_episodelist = QtCore.pyqtSignal()

    def __init__(self, channel_url, ui, update_progress=0):
        QtCore.QThread.__init__(self)
        self.channel_url = channel_url
        self.ui = ui
        self.updateProgress = update_progress
        self.newEpisodeExists = 0
        self.main_directory = os.path.expanduser('~') + '/.brePodder/'

    def run(self):
        # ui.Mutex.lock()
        self.ui.Sem.acquire(1)
        # TODO: SQL--this one is in thread and is making problems
        con = sqlite3.connect(self.main_directory + "podcasts.sqlite", check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()

        self.add_channel(self.channel_url, cur)

        con.commit()
        cur.close()

        if self.newEpisodeExists:
            self.addsignal.emit()

        self.addProgressSignal.emit()

        if self.updateProgress == 0:
            self.addDoneSignal.emit()
        # ui.Mutex.unlock()
        self.ui.Sem.release(1)

    def add_channel(self, new_url=None, cursor=None):
        os.chdir(self.main_directory)
        #
        # print(new_url)
        # print(self.QLineEdit1.text())
        # if not new_url:
        #     feed_link = self.QLineEdit1.text()
        # else:
        #     feed_link = new_url

        feed_link = new_url
        if is_video_link(feed_link):
            feed_link = get_youtube_rss(feed_link)

        print(feed_link)
        headers = {
            'User-Agent': 'brePodder/0.02'
        }
        try:
            resp = requests.get(feed_link, timeout=10.0, headers=headers)
        except requests.ReadTimeout as e:
            print(e)
            # logger.warn("Timeout when reading RSS %s", rss_feed)
            return
        except requests.exceptions.ConnectTimeout as e:
            print(e)
            return
        except requests.exceptions.ConnectionError as e:
            print(e)
            return
        # Put it to memory stream object universal feedparser
        content = BytesIO(resp.content)

        feed_content = feedparser.parse(content)

        # item = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item = QtWidgets.QTreeWidgetItem(self.ui.treeWidget)

        if 'title' in feed_content.feed:
            ChannelTitle = feed_content.feed.title
        elif 'link' in feed_content.feed:
            ChannelTitle = feed_content.feed.link
        else:
            ChannelTitle = feed_link

        if self.ui.db.getChannelByLink(feed_link):
            print(f"channel already exists {feed_link}")
            return

        if self.ui.db.getChannelByTitle(ChannelTitle):
            print(f"channel already exists {ChannelTitle}")
            return

        ChannelDir = self.ui.regex_white_space.sub("", ChannelTitle)
        print("ChannelDir: ")
        print(ChannelDir)
        print(os.getcwd())
        print(self.main_directory + ChannelDir)
        if not os.path.exists(self.main_directory + ChannelDir):
            os.makedirs(self.main_directory + ChannelDir)
        # try:
        #     os.mkdir(ChannelDir)
        # except:
        #     print("directory exists")

        os.chdir(self.main_directory + ChannelDir)
        item.setText(0, ChannelTitle)

        # download Channel logo
        logo_fileBig = ''
        if 'image' in feed_content.feed:
            imageURL = ''
            if feed_content.feed.image.href is not None:
                if feed_content.feed.image.href[0] == '/':
                    imageURL = feed_content.feed.link + feed_content.feed.image.href
                else:
                    imageURL = feed_content.feed.image.href

                # item.setText(1, imageURL)
                # item.setText(5, imageURL)

            # if len(self.ui.downloadList) > 0:
            #     downloadId = self.ui.downloadList[-1][0] + 1
            # else:
            #     downloadId = 0
            #
            # self.ui.itemsDownloading.append((downloadId, imageURL))
            # self.ui.downloadList.append((downloadId, Download(imageURL, item, downloadId, self.ui)))

            url_done = QtCore.QUrl(imageURL)
            fileInfo = QtCore.QFileInfo(url_done.path())
            fileName = fileInfo.fileName()
            # TODO: should we put original or 128px version of logo
            logo_fileBig = ChannelDir + "/" + fileName

            download_image(imageURL, self.main_directory + logo_fileBig)
            self.ui.resize_image(self.main_directory + logo_fileBig, self.main_directory + logo_fileBig)
        # download_image(imageURL,  logo_fileBig)

        #  download favicon
        if "link" in feed_content.feed:
            print(feed_content.feed.link)
            # favicon_url = get_icon_url(w.feed.link)
            favicon_url = get_icon_url("https://" + QtCore.QUrl(feed_content.feed.link).host())
            # favicon_url = get_icon_url(QtCore.QUrl(w.feed.link).host())
        else:
            favicon_url = get_icon_url(feed_link)

        if favicon_url:
            url = favicon_url
        else:
            url = ''
            # url = "https://" + QtCore.QUrl(feed_content.feed.link).host() + "/favicon.ico"

        url_favicon = QtCore.QUrl(url)
        faviconInfo = QtCore.QFileInfo(url_favicon.path())
        favicon = faviconInfo.fileName()
        logo_file = ChannelDir + '/' + favicon

        download_image(url, self.main_directory + logo_file)
        self.ui.resize_image(self.main_directory + logo_file, self.main_directory + logo_file)

        item2 = QtWidgets.QTreeWidgetItem(self.ui.treeWidget)

        if 'title' in feed_content.feed:
            item2.setText(0, feed_content.feed.title)
        else:
            item2.setText(0, "No title")

        item2.setText(1, url)
        item2.setText(5, url)

        if len(self.ui.downloadList) > 0:
            downloadId = self.ui.downloadList[-1][0] + 1
        else:
            downloadId = 0

        self.ui.itemsDownloading.append((downloadId, url))
        self.ui.downloadList.append((downloadId, Download(url, item2, downloadId, self.ui)))

        self.ui.downloadList[downloadId][1].faviconFound = True

        if 'subtitle' in feed_content.feed:
            ChannelSubtitle = feed_content.feed.subtitle
        else:
            ChannelSubtitle = u'No description'

        if 'links' in feed_content.feed:
            ChannelHomepage = feed_content.feed.links[0].href
        #            ChannelHomepage = w.feed.links[1].href
        else:
            ChannelHomepage = 'http://google.com'

        newChannel = (ChannelTitle, feed_link, ChannelHomepage, ChannelSubtitle, logo_file, logo_fileBig)
        self.ui.db.insertChannel(newChannel)

        ChannelId = self.ui.db.getChannelByTitle(ChannelTitle)

        for episode in feed_content.entries:
            self.add_episode(ChannelId[0], episode)

        # self.ui.update_channel_list()
        os.chdir(os.path.expanduser('~') + '/.brePodder')

    def add_episode(self, channel_id, episode):
        new_episode = {'title': '',
                       'enclosure': '',
                       'size': 0,
                       'date': '',
                       'description': '',
                       'status': 'new',
                       'channel_id': channel_id
                       }

        if 'title' in episode:
            new_episode['title'] = episode.title

        if 'enclosures' in episode:
            try:
                new_episode['enclosure'] = episode.enclosures[0].href
                new_episode['size'] = episode.enclosures[0].length
            except IndexError:
                pass
            except AttributeError:
                pass

        if 'yt_videoid' in episode:
            try:
                new_episode['enclosure'] = episode.link
            except AttributeError:
                pass

        if 'updated_parsed' in episode:
            new_episode['date'] = mktime(episode.updated_parsed)
        elif 'published_parsed' in episode:
            new_episode['date'] = mktime(episode.published_parsed)
        else:
            new_episode['date'] = mktime(gmtime())

        if 'summary_detail' in episode:
            try:
                new_episode['description'] = episode.summary_detail.value
            except AttributeError:
                pass

        # print(tuple(new_episode.values()))
        self.ui.db.insertEpisode(tuple(new_episode.values()))


class BrePodder(MainUi):

    def __init__(self):
        MainUi.__init__(self)
        self.headers = {
            'User-Agent': 'brePodder/0.02'
        }

    def memory_usage(self):
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

    def resize_image(self, source_image, destination_image):
        pixmap = QtGui.QPixmap(source_image)
        if pixmap.height() > 300 or pixmap.width() > 300:
            pixmap_resized = pixmap.scaled(300, 300, QtCore.Qt.KeepAspectRatio)
            if not os.path.exists(os.path.dirname(destination_image)):
                os.makedirs(os.path.dirname(destination_image))
            pixmap_resized.save(destination_image)

    def episode_activated(self):
        if self.treeWidget_2.selectedItems():
            selection = self.treeWidget_2.selectedItems()[0]
            try:
                e = self.db.getEpisodeByTitle(selection.text(0))

                if e.get("enclosure"):
                    enc = e.get("enclosure")
                else:
                    enc = 'None'
                if e.get("description"):
                    desc = e.get("description")
                else:
                    desc = 'None'
                if e.get("localfile"):
                    local_file = e.get("localfile")
                else:
                    local_file = 'None'

                self.QTextBrowser1.setHtml("<p>" + desc + "</br>\n\r</p><p><b>FILE: </b><a href=" + enc + ">" + enc + "</a></p>\
                                            <p><b>LOCALFILE: </b><a href=" + local_file + ">" + local_file + "</a></p>\
                                            <p>PLAY:<audio  controls='controls' src='" + enc + "'/></p>")

                self.AudioPlayer.setUrl(enc)
                # ~ if (local_file != 'None') & (AudioPlayer):
                # ~ self.AudioPlayer.setUrl(local_file)
                # ~ else:
                # ~ self.AudioPlayer.setUrl(enc)
            except e:
                print(e)
                print("EpisodeActivated exception")

    def DownloadActivated(self, item, i):
        self.itemZaPrekid = item
        self.actionCancel.setToolTip("Remove Selected Download")
        self.actionPause.setToolTip("Pause Selected Download")
        self.actionResume.setToolTip("Resume Selected Download")

    def EpisodeDoubleClicked(self, episode_row):
        # TODO: change backgroundColor or something else with QBrush
        episode_row.setFont(0, self.fontBold)
        episodeTitle = episode_row.text(0)
        e = self.db.getEpisodeByTitle(episodeTitle)
        channel = self.db.getChannelById(e.get("channel_id"))
        ChannelDir = self.regex_white_space.sub("", channel.get("title"))
        # print "ChannelDir: "
        # print ChannelDir

        os.chdir(os.path.expanduser('~') + '/.brePodder/' + ChannelDir)
        item = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item.setText(0, channel.get("title"))
        item.setText(1, e.get("title"))
        item.setText(2, self.getReadableSize(e.get("size")))
        item.setText(3, '0')
        item.setText(4, '0')

        try:
            item.setText(5, e.get("enclosure"))
        except TypeError:
            print(TypeError)
            item.setText(5, "No link")

        if len(self.downloadList) > 0:
            downloadId = self.downloadList[-1][0] + 1
        else:
            downloadId = 0

        self.itemsDownloading.append((downloadId, e.get("enclosure").replace(" ", "%20")))
        self.downloadList.append((downloadId, Download(e.get("enclosure").replace(" ", "%20"), item, downloadId, self)))

        os.chdir(os.path.expanduser('~') + '/.brePodder')

    def add_channel(self, new_url=None):
        os.chdir(os.path.expanduser('~') + '/.brePodder')
        if not new_url:
            feed_link = self.QLineEdit1.text()
        else:
            feed_link = new_url

        self.QLineEdit1.hide()
        self.QPushButton1.hide()
        self.updateProgressBar.setRange(0, 0)
        self.updateProgressBar.show()
        self.numberOfChannels = 1

        # ch = self.db.getChannelByTitle(self.CurrentChannel)

        # self.ChannelForUpdate = ch

        addChTr = AddChannelThread(feed_link, self, 0)
        addChTr.addsignal.connect(self.update_channel_list, QtCore.Qt.QueuedConnection)
        addChTr.addsignal_episodelist.connect(self.update_episode_list, QtCore.Qt.QueuedConnection)
        addChTr.addDoneSignal.connect(self.adding_channal_done, QtCore.Qt.BlockingQueuedConnection)
        self.update_channel_threads.append(addChTr)
        addChTr.start()
        # updtChTr.append(UpdateChannelThread(i, self, j))
        # self.update_channel_threads.append(updtChTr[j])

    def adding_channal_done(self):
        self.updateProgressBar.hide()
        self.QLineEdit1.show()
        self.QPushButton1.show()

        # self.lightsWorker.stop()
        # self.lightsThread.quit()
        # self.lightsThread.wait()

        self.update_channel_list()
        self.sendMessage("Updating Done")

    def AddChannel(self, new_url=None):
        os.chdir(os.path.expanduser('~') + '/.brePodder')

        print(new_url)
        print(self.QLineEdit1.text())
        if not new_url:
            feed_link = self.QLineEdit1.text()
        else:
            feed_link = new_url

        if is_video_link(feed_link):
            feed_link = get_youtube_rss(feed_link)

        print(feed_link)
        try:
            resp = requests.get(feed_link, timeout=10.0, headers=self.headers)
        except requests.ReadTimeout:
            # logger.warn("Timeout when reading RSS %s", rss_feed)
            return
        except requests.exceptions.ConnectTimeout:
            return
        # Put it to memory stream object universal feedparser
        content = BytesIO(resp.content)

        feed_content = feedparser.parse(content)

        # item = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item = QtWidgets.QTreeWidgetItem(self.treeWidget)

        if 'title' in feed_content.feed:
            ChannelTitle = feed_content.feed.title
        elif 'link' in feed_content.feed:
            ChannelTitle = feed_content.feed.link
        else:
            ChannelTitle = feed_link

        ChannelDir = self.regex_white_space.sub("", ChannelTitle)
        print("ChannelDir: ")
        print(ChannelDir)
        print(os.getcwd())
        try:
            os.mkdir(ChannelDir)
        except:
            print("catch all excetions brePodder.py 567")
            print("directory exists")

        os.chdir(ChannelDir)
        item.setText(0, ChannelTitle)

        # download Channel logo
        logo_fileBig = ''
        if 'image' in feed_content.feed:
            if feed_content.feed.image.href is not None:
                if feed_content.feed.image.href[0] == '/':
                    imageURL = feed_content.feed.link + feed_content.feed.image.href
                else:
                    imageURL = feed_content.feed.image.href

                item.setText(1, imageURL)
                item.setText(5, imageURL)

            if len(self.downloadList) > 0:
                downloadId = self.downloadList[-1][0] + 1
            else:
                downloadId = 0

            self.itemsDownloading.append((downloadId, imageURL))
            self.downloadList.append((downloadId, Download(imageURL, item, downloadId, self)))

            url_done = QtCore.QUrl(imageURL)
            fileInfo = QtCore.QFileInfo(url_done.path())
            fileName = fileInfo.fileName()
            # TODO: should we put original or 128px version of logo
            logo_fileBig = ChannelDir + "/" + fileName
        # download_image(imageURL,  logo_fileBig)

        #  download favicon
        if "link" in feed_content.feed:
            # favicon_url = get_icon_url(w.feed.link)
            favicon_url = get_icon_url("https://" + QtCore.QUrl(feed_content.feed.link).host())
            # favicon_url = get_icon_url(QtCore.QUrl(w.feed.link).host())
        else:
            favicon_url = get_icon_url(feed_link)

        if favicon_url:
            url = favicon_url
        else:
            url = ''
            # url = "https://" + QtCore.QUrl(feed_content.feed.link).host() + "/favicon.ico"

        url_favicon = QtCore.QUrl(url)
        faviconInfo = QtCore.QFileInfo(url_favicon.path())
        favicon = faviconInfo.fileName()
        logo_file = ChannelDir + '/' + favicon

        get_icon(url, logo_file)

        item2 = QtWidgets.QTreeWidgetItem(self.treeWidget)

        if 'title' in feed_content.feed:
            item2.setText(0, feed_content.feed.title)
        else:
            item2.setText(0, "No title")

        item2.setText(1, url)
        item2.setText(5, url)

        if len(self.downloadList) > 0:
            downloadId = self.downloadList[-1][0] + 1
        else:
            downloadId = 0

        self.itemsDownloading.append((downloadId, url))
        self.downloadList.append((downloadId, Download(url, item2, downloadId, self)))

        self.downloadList[downloadId][1].faviconFound = True

        if 'subtitle' in feed_content.feed:
            ChannelSubtitle = feed_content.feed.subtitle
        else:
            ChannelSubtitle = u'No description'

        if 'links' in feed_content.feed:
            ChannelHomepage = feed_content.feed.links[0].href
        #            ChannelHomepage = w.feed.links[1].href
        else:
            ChannelHomepage = 'http://google.com'

        newChannel = (ChannelTitle, feed_link, ChannelHomepage, ChannelSubtitle, logo_file, logo_fileBig)
        self.db.insertChannel(newChannel)

        ChannelId = self.db.getChannelByTitle(ChannelTitle)

        for episode in feed_content.entries:
            self.add_episode(ChannelId[0], episode)

        self.update_channel_list()
        os.chdir(os.path.expanduser('~') + '/.brePodder')

    def add_episode(self, channel_id, episode):
        new_episode = {'title': '',
                       'enclosure': '',
                       'size': 0,
                       'date': '',
                       'description': '',
                       'status': 'new',
                       'channel_id': channel_id
                       }

        if 'title' in episode:
            new_episode['title'] = episode.title

        if 'enclosures' in episode:
            try:
                new_episode['enclosure'] = episode.enclosures[0].href
                new_episode['size'] = episode.enclosures[0].length
            except IndexError:
                pass
            except AttributeError:
                pass

        if 'yt_videoid' in episode:
            try:
                new_episode['enclosure'] = episode.link
            except AttributeError:
                pass

        if 'updated_parsed' in episode:
            new_episode['date'] = mktime(episode.updated_parsed)
        elif 'published_parsed' in episode:
            new_episode['date'] = mktime(episode.published_parsed)
        else:
            new_episode['date'] = mktime(gmtime())

        if 'summary_detail' in episode:
            try:
                new_episode['description'] = episode.summary_detail.value
            except AttributeError as e:
                print("AttributeError", e)
                pass

        # print(tuple(new_episode.values()))
        self.db.insertEpisode(tuple(new_episode.values()))

    def channel_activated(self):
        # selection = self.listWidget.selectedItems()
        selection = self.listWidget.currentItem().text(0)
        print("channel_activated")
        print(selection)

        if selection:
            self.CurrentChannel = selection

        self.update_episode_list(selection)
        try:
            self.update_episode_list(selection)
        except:
            print("catch all excetions brePodder.py 715")
            # if is folder
            pass

            #            self.update_episode_list(selection[0].text(0).toUtf8().data().decode('UTF8'))
            #            self.CurrentChannel = selection[0].text(0).toUtf8().data().decode('UTF8')
            self.actionCancel.setToolTip("Delete Selected Channel")
            self.actionUpdateFeeds.setToolTip("Update Selected Channel")

    def delete_channel(self):
        if self.tab.isVisible():
            try:
                self.db.deleteAllEpisodes(self.CurrentChannel)
                self.db.deleteChannel(self.CurrentChannel)

                os.chdir(os.path.expanduser('~') + '/.brePodder/')
                ChannelDir = os.path.expanduser('~') + '/.brePodder/' + self.regex_white_space.sub("", self.CurrentChannel)

                import shutil
                shutil.rmtree(ChannelDir)
            except:
                print("catch all excetions brePodder.py 736")
                self.db.deleteTaxonomy(self.CurrentChannel)

        self.update_channel_list()

    # last 50 downloadowed episodes
    def update_lastest_episodes_list(self):
        episodes = self.db.getLatestDownloads()
        self.treeWidget_4.clear()

        # self.AudioPlayer_latestDownloads.setUrl( episodes[0][3] )

        for e in episodes:
            item = QtWidgets.QTreeWidgetItem(self.treeWidget_4)
            item.setText(0, str(e[10]))
            item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~') + '/.brePodder/' + e[14])))
            item.setText(1, e[1])
            item.setText(2, self.getReadableSize(e[4]))
            item.setText(3, os.path.expanduser('~') + '/.brePodder/' + str(e[3]))

    # newest episodes
    def update_newest_episodes_list(self):
        episodes = self.db.getLatestEpisodes()
        self.treeWidget_5.clear()

        # self.AudioPlayer_newestEpisodes.setUrl( episodes[0][2] )

        for e in episodes:
            item = QtWidgets.QTreeWidgetItem(self.treeWidget_5)
            item.setText(0, e[10])
            item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~') + '/.brePodder/' + e[15])))
            item.setText(1, e[1])
            if e[4]:
                item.setText(2, self.getReadableSize(e[4]))
            else:
                item.setText(2, '???')
            try:
                b = gmtime(float(e[5]))
                epDate = strftime("%x", b)
            except:
                print("catch all excetions brePodder.py 776")
                b = gmtime()
                epDate = strftime("%x", b)

            item.setText(3, epDate)

            if e[2] and e[2] is not None:
                item.setText(4, e[2])

    # TODO: Send file to some media player
    def LastestEpisodeDoubleClicked(self, a):
        # os.system( "mocp -a " + a.text(3).toUtf8().data().decode('UTF8') )
        self.AudioPlayer_latestDownloads.setUrl(a.text(3))
        self.AudioPlayer_latestDownloads.playClicked()

    def LastestEpisodeActivated(self, a):
        # os.system( "mocp -a " + a.text(3).toUtf8().data().decode('UTF8') )
        # self.AudioPlayer_latestDownloads.setUrl( a.text(3).toUtf8().data().decode('UTF8') )
        pass

    def NewestEpisodeClicked(self, item):
        episode = item.text(4)
        self.AudioPlayer_newestEpisodes.setUrl(episode)

    def NewestEpisodeDoubleClicked(self, a):
        # print  a.text(4).toUtf8().data().decode('UTF8')
        episode = a.text(4)
        # print episode.get("enclosure")
        print(episode + " added to queue")
        self.AudioPlayer_newestEpisodes.setUrl(episode)
        self.AudioPlayer_newestEpisodes.play()

    def getReadableSize(self, size):
        if size:
            if (size) > 1024 * 1024:
                try:
                    sizeReadable = str(size / 1024 / 1024) + ' MB'
                except:
                    print("catch all excetions brePodder.py 814")
                    sizeReadable = size
            elif (size) > 1024:
                sizeReadable = str(size / 1024) + ' kB'
            else:
                sizeReadable = str(size) + ' B'
        else:
            sizeReadable = 'None'
        return sizeReadable

    def update_episode_list(self, channel_Title):
        print("update_episode_list")

        print(self.db.is_folder(channel_Title))

        if self.db.is_folder(channel_Title):
            tt = self.db.getFolderEpisodes(channel_Title)
        else:
            tt = self.db.getChannelEpisodes(channel_Title)
            cc = self.db.getChannelByTitle(channel_Title)
            if cc:
                self.QTextBrowser1.setHtml("<p>" + cc[4] + "</p>     <p> <b>Feed link:</b> <a href=" + cc[2] + ">" + cc[
                    2] + "</a></p> <p><b>Homepage: </b><a href=" + cc[3] + ">" + cc[3] + "</a></p>")
            else:
                return
        self.treeWidget_2.clear()
        for t in tt:
            item2 = QtWidgets.QTreeWidgetItem(self.treeWidget_2)

            if not t[3]:  # .localfile:
                item2.setIcon(0, QtGui.QIcon(":/icons/build.png"))
            else:
                item2.setIcon(0, QtGui.QIcon(":/icons/mp3.png"))
            item2.setText(0, t[1])  # .title
            item2.setText(1, self.getReadableSize(t[4]))  # .size
            try:
                b = gmtime(float(t[5]))  # .date
                epDate = strftime("%x", b)
            except:
                print("catch all excetions brePodder.py 846")
                b = gmtime()
                epDate = strftime("%x", b)
                print("date exception")
            item2.setText(2, epDate)

            if t[7] == 'new':
                item2.setFont(0, self.fontBold)

    def update_channel_list(self):
        channels = self.db.getAllChannelsWOFolder()
        folders = self.db.getAllFolders()

        self.listWidget.clear()

        for folder in folders:
            itemF = QtWidgets.QTreeWidgetItem(self.listWidget)
            itemF.setText(0, folder[1])
            itemF.setIcon(0, QtGui.QIcon(':/icons/folder-blue.png'))
            itemF.setFlags(enabled | droppable)
            itemF.setExpanded(True)
            #            cur.execute('select * from sql_channel where folder_id = ?',(folder[0],))
            #            childChannels = cur.fetchall()
            childChannels = self.db.getFolderChannels(folder[0])

            for childChannel in childChannels:
                itemChildChannel = QtWidgets.QTreeWidgetItem(itemF)
                itemChildChannel.setText(0, childChannel[1])
                # print "Ch. icon: "
                # print os.path.expanduser('~') + '/.brePodder/' + childChannel[5]
                itemChildChannel.setIcon(0, QtGui.QIcon(
                    QtGui.QPixmap(os.path.expanduser('~') + '/.brePodder/' + childChannel[6])))
                itemF.addChild(itemChildChannel)

        for channel in channels:
            item = QtWidgets.QTreeWidgetItem(self.listWidget)
            #            if channel.episode[-1].status == u'new':
            #                item.setFont(0, self.fontBold)
            item.setText(0, channel[1])
            # ~ print(channel[6])
            item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~') + '/.brePodder/' + channel[6])))
            #            item.setToolTip(0,"<p><img src="+"'"+channel.logobig+"'"+"></p><p style='font-size:20pt'><b>"+channel.title+"</b></p><a href="+channel.link+">"+channel.link+"</a>")
            item.setFlags(enabled | draggable | selectable)

    # dodati bold za channel koji ima novu epizodu. mislim da je to najefikasnije preko novog polja u bazi.

    #        self.cur.close()

    def updateProgressBarFromThread(self):
        self.updateProgressBar.setValue(self.updateProgressBar.value() + 1)
        if self.updateProgressBar.value() == self.numberOfChannels - 1:
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
        self.updateProgressBar.setRange(0, 0)
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

        self.ChannelForUpdate = ch
        #        print ch.title
        #        ui.Sem.acquire()

        updtChTr = UpdateChannelThread(ch, self, 0)
        updtChTr.updatesignal.connect(self.update_channel_list, QtCore.Qt.QueuedConnection)
        updtChTr.updatesignal_episodelist.connect(self.update_episode_list, QtCore.Qt.QueuedConnection)
        updtChTr.updateDoneSignal.connect(self.update_done, QtCore.Qt.BlockingQueuedConnection)
        self.update_channel_threads = updtChTr
        updtChTr.start()

    def update_all_channels(self):
        self.QLineEdit1.hide()
        self.QPushButton1.hide()

        self.updateProgressBar.show()

        updtChTr = []
        #        allChannels=Channel.query.all()

        #        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        #        con.isolation_level = None
        #        cur = con.cursor()
        #        cur.execute('select * from sql_channel')
        #        allChannels = cur.fetchall()

        allChannels = self.db.getAllChannels()

        self.numberOfChannels = allChannels.__len__() - 1
        self.updateProgressBar.setRange(0, self.numberOfChannels + 1)
        self.updateProgressBar.setValue(0)
        self.updateProgressBar.setFormat("%v" + " of " + "%m")
        j = 0
        for i in allChannels:
            updtChTr.append(UpdateChannelThread(i, self, j))
            self.update_channel_threads.append(updtChTr[j])
            # QtCore.QObject.connect(updtChTr[j],QtCore.SIGNAL("updateProgressSignal"),self.updateProgressBarFromThread,QtCore.Qt.BlockingQueuedConnection)
            updtChTr[j].updateProgressSignal.connect(self.updateProgressBarFromThread,
                                                     QtCore.Qt.BlockingQueuedConnection)
            updtChTr[j].start()
            j = j + 1

    def sendMessage(self, message):
        try:
            print(message)
            # import pynotify
            # if pynotify.init("brePodder"):
            #    n = pynotify.Notification("brePodder", message)
        #                n = pynotify.Notification("Title", "message", "icon-name")
        #    n.show()
        # else:
        #    print "there was a problem initializing the pynotify module"
        except:
            print("catch all excetions brePodder.py 985")
            print("you don't seem to have pynotify installed")

    def update_done(self):
        self.updateProgressBar.hide()
        self.QLineEdit1.show()
        self.QPushButton1.show()

        # self.lightsWorker.stop()
        # self.lightsThread.quit()
        # self.lightsThread.wait()

        self.update_channel_list()
        self.sendMessage("Updating Done")