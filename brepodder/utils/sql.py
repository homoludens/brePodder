import sqlite3
import os
import sys

class DBOperation():
    def __init__(self):
        self.db = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite",  check_same_thread=False, timeout=20)
        self.db.isolation_level = None
        self.cur = self.db.cursor()
        self.cur.row_factory = sqlite3.Row
        # self.create_db()

    def insertChannel(self, channel):

        # con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread=False, timeout=20)
        # con.isolation_level = None
        # cur = con.cursor()
        # cur.execute('insert into sql_channel(title, link, homepage, description, logo, logobig) values (?,?,?,?,?,?) ', channel)
        # cur.close()

        # self.cur = self.db.cursor()
        self.cur.execute('insert into sql_channel(title, link, homepage, description, logo, logobig) values (?,?,?,?,?,?) ', channel)
        # self.db.commit()
        # return True

    def close(self):
        self.db.commit()
        self.cur = self.db.cursor()
        pass
        # self.db.commit()
        # self.cur.close()

    def getFolderChannels(self,  folder):
        self.cur.execute('select * from sql_channel where folder_id = ?', (folder,))
        child_channels = self.cur.fetchall()
        # self.db.commit()
        return child_channels

    def getChannelById(self,  channel_id):
        channel = self.cur.execute('select * from sql_channel where id = ?', (channel_id,)).fetchone()
        # self.db.commit()
        return dict(channel)

    def getChannelByTitle(self,  channel_title):
        channel = self.cur.execute('select * from sql_channel where title = ?', (channel_title,)).fetchone()
        # self.db.commit()
        return channel

    def getChannelByLink(self,  channel_link):
        channel = self.cur.execute('select * from sql_channel where link = ?', (channel_link,)).fetchone()
        # self.db.commit()
        return channel

    def getChannelByFeed(self,  channel):
        channel = self.cur.execute('select * from sql_channel where title = ?', (channel,))
        # self.db.commit()
        return channel

    def getEpisodeByTitle(self,  episodeTitle):
        episode = self.cur.execute('select * from sql_episode where title = ?', (episodeTitle,)).fetchone()
        # self.db.commit()
        return dict(episode)

    def getAllChannels(self):
        channels = self.cur.execute('select * from sql_channel').fetchall()
        # self.db.commit()
        return channels

    def getAllChannelsLinks(self):
        channels = self.cur.execute('select link from sql_channel').fetchall()
        # self.db.commit()
        return channels

    def getAllChannelsWOFolder(self):
        channels = self.cur.execute('select * from sql_channel where folder_id IS NULL ORDER BY title').fetchall()
        # self.db.commit()
        return channels

    def is_folder(self, title):
        test = self.cur.execute(f"select * from sql_taxonomy WHERE title='{title}'").fetchall()
        # self.db.commit()
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
        # self.db.commit()
        return episodes

    def getAllFolders(self):
        folders = self.cur.execute('select * from sql_taxonomy ORDER BY title').fetchall()
        # self.db.commit()
        return folders

    def getCurrentChannel(self, channel_title):
        channel = self.getChannelByTitle(channel_title)
        channel_result = self.cur.execute('select id,title,status from sql_episode where channel_id = ?', (channel[0],))
        result = channel_result.fetchall()
        # self.db.commit()
        return channel, result

    def insertFolder(self,  FolderName):
        self.cur.execute('insert into sql_taxonomy(title) values (?)', (FolderName,))
        # self.db.commit()
        return True

    def getLatestDownloads(self):
        self.cur.execute('SELECT * FROM sql_episode EP, sql_channel CH WHERE EP.channel_id = CH.id AND EP.status="downloaded" ORDER BY date DESC LIMIT 50')
        episodes = self.cur.fetchall()
        # self.db.commit()
        return episodes

    def getLatestEpisodes(self):
        self.cur.execute('SELECT * FROM sql_episode EP, sql_channel CH WHERE EP.channel_id = CH.id  ORDER BY date DESC LIMIT 50')
        episodes = self.cur.fetchall()
        # self.db.commit()
        return episodes

    def getChannelEpisodes(self,  channelTitle):
        self.cur.execute('SELECT * FROM sql_episode EP, sql_channel CH WHERE EP.channel_id = CH.id AND CH.title = (?) ORDER BY date DESC LIMIT 50',  (channelTitle,))
        episodes = self.cur.fetchall()
        # self.db.commit()
        return episodes

    def insertEpisode(self, ep):
        self.cur.execute('insert into sql_episode(title, enclosure, size, date, description, status, channel_id) values (?,?,?,?,?,?,?) ', ep)
        # self.db.commit()

    def updateEpisode(self,  episode):
        self.cur.execute('update sql_episode set localfile = ?, status = ?  where id = ?', episode)
        # self.db.commit()

    def updateEpisodeStatus(self, episodeId):
        self.cur.execute('update  sql_episode set status= "old" where sql_episode.id = ?', (episodeId,))
        self.db.commit()

    def deleteAllEpisodes(self, channelTitle):
        channel_id = self.getChannelByTitle(channelTitle)
        try:
            self.cur.execute('delete from  sql_episode where channel_id = ?', (channel_id[0],))
        except:
            e = sys.exc_info()
            print(e)
            print("exception sql.py 183")
            pass
        self.db.commit()

    def deleteChannel(self, channelTitle):
        channel_id = self.getChannelByTitle(channelTitle)
        self.cur.execute('delete from  sql_channel where id = ?', (channel_id[0], ))
        self.db.commit()

    def deleteTaxonomy(self, folderTitle):
        self.cur.execute('delete from  sql_taxonomy where title = ?', (folderTitle,))
        self.db.commit()

    def addChannelToFolder(self, channel_title, folder_title):
        self.cur.execute('select id from sql_channel where title = ?', [channel_title, ])
        channel_id = self.cur.fetchone()[0]
        if not folder_title:
            self.cur.execute('update sql_channel set folder_id = NULL  where id = :ch_id', {"ch_id": channel_id})
        else:
            self.cur.execute('select * from sql_channel where title = ?', (folder_title,))
            cc = self.cur.fetchone()
            if not cc:
                self.cur.execute('select id from sql_taxonomy where title = ?', (folder_title,))
                tx_id = self.cur.fetchone()[0]
            else:
                tx_id = cc[7]
            self.cur.execute('update sql_channel set folder_id = :tx_id  where id = :ch_id', {"tx_id": tx_id, "ch_id": channel_id})
        self.db.commit()

    def create_db(self):
        try:
            self.cur.execute('''CREATE TABLE IF NOT EXISTS sql_channel (
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

        except sqlite3.OperationalError:
            print("table sql_channel already exists")

        try:
            self.cur.execute('''CREATE TABLE IF NOT EXISTS sql_episode (
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
        except sqlite3.OperationalError:
            print("table sql_channels already exists")

        try:
            self.cur.execute('''CREATE TABLE IF NOT EXISTS sql_taxonomy (
                            id INTEGER NOT NULL,
                            title VARCHAR(60),
                            PRIMARY KEY (id)
                        )''')
        except sqlite3.OperationalError:
            print("table sql_channels already exists")
        self.db.commit()
