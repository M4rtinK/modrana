#!/usr/bin/python
#----------------------------------------------------------------------------
# Module handling text entry.
#----------------------------------------------------------------------------
# Copyright 2010, Martin Kolman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------------
from base_module import ranaModule
import gtk

def getModule(m,d):
  return(textEntry(m,d))

class textEntry(ranaModule):
  """A module for hadnling text entry."""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    
  def update(self):
    # Get and set functions are used to access global data
    self.set('num_updates', self.get('num_updates', 0) + 1)
    #print "Updated %d times" % (self.get('num_updates'))

  def clearEntry(self):
    self.set('textEntry', None)
    self.set('textEntryDone', False)

  def respondToTextEntry(self, entry, dialog, response,instance,key):
      print "responding to text entry"
#      self.set('textEntry', entry.get_text())
#      self.set('textEntryDone', True)
      self.respond(entry.get_text(), instance,key)
      print "text entry dialog is quiting"
      dialog.destroy()

  def respondToDialog(self, dialog, response_id,entry,instance,key):
      print "responding to dialog"
#      self.set('textEntry', entry.get_text())
#      self.set('textEntryDone', True)
      self.respond(entry.get_text(), instance,key)
      print "text entry dialog is quiting"
      dialog.destroy()

  def respond(self, result, instance, key):
    instance.handleTextEntryResult(key,result)


  def entryBox(self, instance,key, label="Text entry", initialText=""):
      dialog = gtk.Dialog(
        label,
        None,
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
#        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
#                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        )
#      dialog = gtk.MessageDialog(
#        None,
#        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
#        gtk.MESSAGE_QUESTION,
#        gtk.BUTTONS_OK,
#        None)
#      dialog.set_markup('Please enter your <b>name</b>:')
      #create the text input field
      entry = gtk.Entry()
      entry.set_text(initialText)
      #allow the user to press enter to do ok
      entry.connect("activate", self.respondToTextEntry, dialog, gtk.RESPONSE_OK, instance,key)
      dialog.connect("response", self.respondToDialog,entry, instance,key)
      #create a horizontal box to pack the entry and a label
      hbox = gtk.HBox()
      hbox.pack_start(gtk.Label(), False, 5, 5)
      hbox.pack_end(entry)
      #some secondary text
#      dialog.format_secondary_markup("This will be used for <i>identification</i> purposes")
      #add it and show it
      dialog.vbox.pack_end(hbox, True, True, 0)
      self.clearEntry()
      (width, height) = dialog.get_size() # get the current size
      (x,y,w,h) = self.get('viewport')
      dialog.resize(w,height) # resize the dialog to the width of the window and leave height the same
      dialog.show_all()


if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
