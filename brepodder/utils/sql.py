import sqlite3
import os


class DBOperation():
    def __init__(self):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite",  check_same_thread=False)
        con.isolation_level = "IMMEDIATE"
        self.cur = con.cursor()
        self.create_db()

    #TODO: ovo ne radi
    def insertChannel(self, channel):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False, timeout=20)
        con.isolation_level = None
        cur = con.cursor()
        cur.execute('insert into sql_channel(title, link, homepage, description, logo, logobig) values (?,?,?,?,?,?) ', channel)
        cur.close()
        #print "insertChannel: "
        #print channel

#    def insertEpisode(self, episode):
#        self.cur.execute('insert into sql_episode(title, enclosure, size, date, description, status, channel_id) values (?,?,?,?,?,?,?) ', episode)

    def close(self):
        self.cur.close()

    def getFolderChannels(self,  folder):
        self.cur.execute('select * from sql_channel where folder_id = ?', (folder,))
        childChannels = self.cur.fetchall()
        return childChannels

    def getChannelById(self,  channel_id):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = "IMMEDIATE"
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute('select * from sql_channel where id = ?', (channel_id,))
        channel = cur.fetchone()
        cur.close()

        return dict(channel)

    def getChannelByTitle(self,  channel_title):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = "IMMEDIATE"
        cur = con.cursor()
        cur.execute('select * from sql_channel where title = ?', (channel_title,))
        cc = cur.fetchone()
        cur.close()

        return cc

    def getChannelByLink(self,  channel_link):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = "IMMEDIATE"
        cur = con.cursor()
        cur.execute('select * from sql_channel where link = ?', (channel_link,))
        cc = cur.fetchone()
        cur.close()

        return cc

    def getChannelByFeed(self,  channel):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = "IMMEDIATE"
        cur = con.cursor()
        cur.execute('select * from sql_channel where title = ?', (channel,))
        cc = cur.fetchone()
        cur.close()

        return cc

    def getEpisodeByTitle(self,  episodeTitle):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = "IMMEDIATE"
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute('select * from sql_episode where title = ?',(episodeTitle,))
        episode = cur.fetchone()
        episodeDict = dict(episode)
        cur.close()

        return episodeDict

#    def GETCHANNEL(self,  channel):
#        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = True)
#        con.isolation_level = "IMMEDIATE"
#        cur = con.cursor()
#        cur.execute('select * from sql_channel where title = ?',(channel,))
#        cc = cur.fetchone()
#        cur.close()
#
#        return cc

#    def getChannel(self,  channel):
#        self.cur.execute('select * from sql_channel where title = ?',(channel, ))
#        ch = self.cur.fetchone()
#        return ch

    def getAllChannels(self):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()
        cur.execute('select * from sql_channel')
        channels = cur.fetchall()

        return channels

    def getAllChannelsLinks(self):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()
        cur.execute('select link from sql_channel')
        channels = cur.fetchall()

        return channels

    def getAllChannelsWOFolder(self):
        self.cur.execute('select * from sql_channel where folder_id IS NULL ORDER BY title')
        channels = self.cur.fetchall()

        return channels

    def is_folder(self, title):
        test = self.cur.execute(f"select * from sql_taxonomy WHERE title='{title}'").fetchall()
        if test:
            return True
        return False

    def getFolderEpisodes(self, channel_title):
        query = f"""
        SELECT EP.id, (CH.title || " - " || EP.title), EP.enclosure, EP.localfile, EP.size, EP.date, EP.description, EP.channel_id 
        FROM sql_episode EP 
        JOIN sql_channel CH  ON EP.channel_id = CH.id
        JOIN sql_taxonomy FLD ON CH.folder_id = FLD.id
        WHERE FLD.title = ('{channel_title}') ORDER BY date DESC LIMIT 150
        """
        episodes = self.cur.execute(query).fetchall()
        print("getFolderEpisodes", channel_title, episodes)
        return episodes


    def getAllFolders(self):
        self.cur.execute('select * from sql_taxonomy ORDER BY title')
        folders = self.cur.fetchall()

        return folders

    def getCurrentChannel(self, ch):
#        cc = self.cur.execute('select id,title,link from sql_channel where title =?', (ch,))
#        a = cc.fetchone()
        a = self.getChannelByTitle(ch)
        tt_1 = self.cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0], ))
        tt = tt_1.fetchall()
#        print 'tt'
#        print tt
        return a, tt

    def insertFolder(self,  FolderName):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        con.isolation_level = None
        cur = con.cursor()
        cur.execute('insert into sql_taxonomy(title) values (?)', (FolderName,))
        cur.close()
#        self.cur.execute('insert into sql_taxonomy(title) values (?)', (FolderName,))
#        self.cur.close()

#    def getChannel(self, ch):
#        cc = self.cur.execute('select id,title,link from sql_channel where title =?', (ch,))
#        a = cc.fetchone()
#        tt = self.cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0],))
#        return a, tt

    def getLatestDownloads(self):
        self.cur.execute('SELECT * FROM sql_episode EP, sql_channel CH WHERE EP.channel_id = CH.id AND EP.status="downloaded" ORDER BY date DESC LIMIT 50')
        episodes = self.cur.fetchall()

        return episodes

    def getLatestEpisodes(self):
        self.cur.execute('SELECT * FROM sql_episode EP, sql_channel CH WHERE EP.channel_id = CH.id  ORDER BY date DESC LIMIT 50')
        episodes = self.cur.fetchall()

        return episodes

    def getChannelEpisodes(self,  channelTitle):
        self.cur.execute('SELECT * FROM sql_episode EP, sql_channel CH WHERE EP.channel_id = CH.id AND CH.title = (?) ORDER BY date DESC LIMIT 50',  (channelTitle,))
        episodes = self.cur.fetchall()
        return episodes

    def insertEpisode(self, ep):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False, timeout=20)
        con.isolation_level = None
        cur = con.cursor()
        cur.execute('insert into sql_episode(title, enclosure, size, date, description, status, channel_id) values (?,?,?,?,?,?,?) ', ep)
        cur.close()

    def updateEpisode(self,  episode):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()
        cur.execute('update sql_episode set localfile = ?, status = ?  where id = ?', episode)
        cur.close()
#        self.cur.execute('update  sql_episode set status= "old" where sql_episode.id = ?',(epId,) )

    def updateEpisodeStatus(self, episodeId):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = "IMMEDIATE"
        cur = con.cursor()
        cur.execute('update  sql_episode set status= "old" where sql_episode.id = ?', (episodeId,))
        cur.close()

    def deleteAllEpisodes(self, channelTitle):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()
        channel_id = self.getChannelByTitle(channelTitle)
        try:
            cur.execute('delete from  sql_episode where channel_id = ?', (channel_id[0],))
        except:
            print("exception sql.py 183")
            pass
        cur.close()

    def deleteChannel(self, channelTitle):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()
        channel_id = self.getChannelByTitle(channelTitle)
        cur.execute('delete from  sql_channel where id = ?', (channel_id[0], ))
        cur.close()

    def deleteTaxonomy(self, folderTitle):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()
        cur.execute('delete from  sql_taxonomy where title = ?', (folderTitle,))
        cur.close()

    def addChannelToFolder(self, channelTitle, folderTitle):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()
        cur.execute('select id from sql_channel where title = ?', [channelTitle, ])
        ch_id = cur.fetchone()[0]

        if not folderTitle:
            cur.execute('update sql_channel set folder_id = NULL  where id = :ch_id', {"ch_id": ch_id})
        else:
            cur.execute('select * from sql_channel where title = ?', (folderTitle,))
            cc = cur.fetchone()
            if not cc:
                cur.execute('select id from sql_taxonomy where title = ?', (folderTitle,))
                tx_id = cur.fetchone()[0]
            else:
                tx_id = cc[7]

            cur.execute('update sql_channel set folder_id = :tx_id  where id = :ch_id', {"tx_id": tx_id, "ch_id": ch_id})
        con.commit()
        cur.close()

    def create_db(self):
        print("create_db")
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()
        # cur = self.cur
        try:
            cur.execute('''CREATE TABLE IF NOT EXISTS sql_channel (
                                id INTEGER NOT NULL,
                                title VARCHAR(30),
                                link VARCHAR(256),
                                homepage VARCHAR(256),
                                description VARCHAR(4096),
                                logo VARCHAR(256),
                                logobig VARCHAR(256), folder_id INTEGER,
                                folder INTEGER,
                                PRIMARY KEY (id)
                        )''')
            con.commit()
           # cur.close()
        except sqlite3.OperationalError:
            print("table sql_channel already exists".format(self.table))

        try:
            cur.execute('''CREATE TABLE IF NOT EXISTS sql_episode (
                                id INTEGER NOT NULL,
                                title VARCHAR(60),
                                enclosure VARCHAR(256),
                                localfile VARCHAR(256),
                                size INTEGER,
                                date VARCHAR(256),
                                description VARCHAR(4096),
                                status VARCHAR(16),
                                channel_id INTEGER,
                                PRIMARY KEY (id),
                                 CONSTRAINT sql_episode_channel_id_fk FOREIGN KEY(channel_id) REFERENCES sql_channel (id)
                            )''')

            con.commit()
            #cur.close()
        except sqlite3.OperationalError:
            print("table sql_channels already exists".format(self.table))

        try:
            cur.execute('''CREATE TABLE IF NOT EXISTS sql_taxonomy (
                            id INTEGER NOT NULL,
                            title VARCHAR(60),
                            PRIMARY KEY (id)
                        )''')

            con.commit()
            cur.close()
        except sqlite3.OperationalError:
            print("table sql_channels already exists".format(self.table))