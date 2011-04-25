from elixir import *
import sqlalchemy
import sys
import sqlite3,  os

sys.setappdefaultencoding('utf-8') 


metadata.bind = "sqlite:////home/homoludens/.brePodder/podcasts.sqlite"
metadata.bind.echo = False
#options_defaults['autosetup'] = True

setup_all()

class BaseOperation():
    def __init__(self):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite",  check_same_thread = False)
        con.isolation_level = None
        self.cur = con.cursor()
        
    def getCurrentChannel(self, ch):
        cc = self.cur.execute('select id,title from sql_channel where title =?', (ch[1],))
        a = cc.fetchone()
        tt = self.cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0]))
        return a, tt
        
    def getChannel(self, ch):    
        cc = self.cur.execute('select id,title,link from sql_channel where title =?', (ch[1],))
        a = cc.fetchone()
        tt = self.cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0],))
        return a, tt
        
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


