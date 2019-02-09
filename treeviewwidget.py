from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork #, QtWebKit
import sqlite3




#override QTreeViewWidget for handling Drag & Drop events
class treeViewWidget( QtWidgets.QTreeWidget ):
    def __init__(self, parent=None):
      super(treeViewWidget, self).__init__(parent)
      self.setAcceptDrops(True)
      self.setDragEnabled(True)
      self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
      self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
      self.sortByColumn(0, 0)

    def dropEvent(self, event):
        if self.itemAt( event.pos() ).flags() & droppable:
#            what = self.selectedItems()[0].text(0)
#            where = self.itemAt(event.pos()).text(0)
#            ch=Channel.query.filter_by(title=self.selectedItems()[0].text(0)).one()
#            tx=Taxonomy.query.filter_by(title=self.itemAt(event.pos()).text(0)).one()

            #TODO: SQL-- this on is out of scope and can not get to db object
            con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
            con.isolation_level = None
            cur = con.cursor()
            cur.execute('select id from sql_channel where title = ?', [self.selectedItems()[0].text(0),])
            ch_id = cur.fetchone()[0]
            cur.execute('select id from sql_taxonomy where title = ?', ( self.itemAt(event.pos()).text(0), ) )
            tx_id = cur.fetchone()[0]
            cur.execute('update sql_channel set folder_id = :tx_id  where id = :ch_id', {"tx_id": tx_id, "ch_id": ch_id})
            con.commit()
            cur.close()
#            channelTitle = self.selectedItems()[0].text(0).toUtf8().data()
#            folderTitle = self.itemAt(event.pos()).text(0).toUtf8().data()
#            self.parent.db.addChannelToFolder(self,  channelTitle,  folderTitle)

#            ui.update_channel_list()
        else:
            print('not folder')
            con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
            con.isolation_level = None
            cur = con.cursor()
            cur.execute('select id from sql_channel where title = ?', [self.selectedItems()[0].text(0),])
            ch_id = cur.fetchone()[0]
            cur.execute('update sql_channel set folder_id = NULL  where id = :ch_id', {"ch_id": ch_id})
            con.commit()
            cur.close()

#      print dir(event)
#      event.setDropAction(QtCore.Qt.MoveAction)
#      event.accept()

    def dropMimeData(self, parent, row, data, action):
        if action == QtCore.Qt.MoveAction:
            return self.moveSelection(parent, row)
        return False

    def dragEnterEvent(self, event):
            event.accept()
            print('drag')

