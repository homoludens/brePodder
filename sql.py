from elixir import *
import sqlalchemy
import sys
sys.setappdefaultencoding('utf-8') 

metadata.bind = "sqlite:////home/homoludens/.brePodder/podcasts.sqlite"
metadata.bind.echo = False
options_defaults['autosetup'] = True

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

setup_all(True)


