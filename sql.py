from elixir import *
import sqlalchemy
import sys
import sqlite3,  os

sys.setappdefaultencoding('utf-8') 


metadata.bind = "sqlite:////home/homoludens/.brePodder/podcasts.sqlite"
metadata.bind.echo = False
#options_defaults['autosetup'] = True

setup_all()

class DBOperation():
    def __init__(self):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite",  check_same_thread = False)
        con.isolation_level = "IMMEDIATE"
        self.cur = con.cursor()

    def updateEpisodeStatus(self, episodeId):
        self.cur.execute('update  sql_episode set status= "old" where sql_episode.id = ?',(episodeId,) )

    def insertEpisode(self, episode):              
        self.cur.execute('insert into sql_episode(title, enclosure, size, date, description, status, channel_id) values (?,?,?,?,?,?,?) ', episode)

    def close(self):
        self.cur.close()
    
    def getFolderChannels(self,  folder):
        self.cur.execute('select * from sql_channel where folder_id = ?',(folder,))
        childChannels = self.cur.fetchall()
        return childChannels


    def getChannelByTitle(self,  channel):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        con.isolation_level = "IMMEDIATE"
        cur = con.cursor()       
        cur.execute('select * from sql_channel where title = ?',(channel,))
        cc = cur.fetchone()
        cur.close()
        
        return cc

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
        self.cur.execute('select * from sql_channel')
        channels = self.cur.fetchall()
        
        return channels
    
    def getAllChannelsWOFolder(self):
        self.cur.execute('select * from sql_channel where folder_id IS NULL')
        channels = self.cur.fetchall()
        
        return channels
    
    def getAllFolders(self):
        self.cur.execute('select * from sql_taxonomy')
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
        
#    def getChannel(self, ch):    
#        cc = self.cur.execute('select id,title,link from sql_channel where title =?', (ch,))
#        a = cc.fetchone()
#        tt = self.cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0],))
#        return a, tt
    def getLatestDownloads(self):
        self.cur.execute('SELECT * FROM sql_episode WHERE status="downloaded" ORDER BY date DESC LIMIT 50')
        episodes = self.cur.fetchall()

        return episodes


    def getLatestEpisodes(self):
        self.cur.execute('SELECT * FROM sql_episode EP, sql_channel CH WHERE EP.channel_id = CH.id ORDER BY date DESC LIMIT 50')
        episodes = self.cur.fetchall()
        return episodes

    def insertEpisode(self, ep):       
        self.cur.execute('insert into sql_episode(title, enclosure, size, date, description, status, channel_id) values (?,?,?,?,?,?,?) ', ep)

    def updateEpisode(self,  epId):
        self.cur.execute('update  sql_episode set status= "old" where sql_episode.id = ?',(epId,) )

class Channel(Entity):
    title = Field(Unicode(30))
    link = Field(Unicode(256))
    homepage = Field(Unicode(256))
    description = Field(Unicode(4096))
    logo = Field(Unicode(256))
    logobig = Field(Unicode(256))
    episode = OneToMany('Episode')    # <-- add this line
    folder = ManyToOne('Taxonomy') 
    
    def __repr__(self):
        return ' "%s" (%s) ' % (self.title,self.link)
        
#    using_table_options(UniqueConstraint('title'))
    
class Episode(Entity):
    title = Field(Unicode(60))
    enclosure = Field(Unicode(256))
    localfile = Field(Unicode(256))
    size=Field(Integer)
    date = Field(String(256))
    description = Field(Unicode(4096))
    status=Field(Unicode(16)) #status epizode: new, downloaded, deleted, old
    channel = ManyToOne('Channel', ondelete="cascade")         # <-- and this one
    
class Taxonomy(Entity):
    title = Field(Unicode(60))
    folder = OneToMany('Channel')

setup_all()

setup_all(True)


