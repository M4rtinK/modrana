# -*- coding: utf-8 -*-
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
from modules.base_module import ranaModule

# only import GKT libs if GTK GUI is used
from core import gs
if gs.GUIString == "GTK":
  import gtk

def getModule(m,d,i):
  return(textEntry(m,d,i))

class textEntry(ranaModule):
  """A module for handling text entry."""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.entryBoxVisible = False
    

  def clearEntry(self):
    self.set('textEntry', None)
    self.set('textEntryDone', False)

  def respondToTextEntry(self, entry, dialog, response,instance,key, persistentKey):
      self.respond(entry.get_text(), instance,key, persistentKey)
      dialog.destroy()

  def respondToDialog(self, dialog, response_id,entry,instance,key, persistentKey): 
      print "responding to dialog"
      if response_id == gtk.RESPONSE_ACCEPT:
        print("** dialog accepted **")
        self.respond(entry.get_text(), instance,key, persistentKey)
      else:
        print("** dialog rejected **")
        """the dialog was rejected so we don't
        report the input that could have been entered"""
      dialog.destroy()

  def respond(self, result, instance, key, persistentKey=None):
    if persistentKey is not None:
      self.set(persistentKey, result)
    self.dmod.textEntryDone()
    instance.handleTextEntryResult(key,result)
    self.entryBoxVisible = False

  def entryBox(self, instance,key, label="Text entry", initialText="", description=None, persistentKey=None):
      dialog = gtk.Dialog(
        label,
        None,
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
        (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        )
      #create the text input field
      entry = gtk.Entry()
      # reload last used input, if available
      if persistentKey is not None:
        initialText = self.get(persistentKey, initialText)
      # make sure the initialText is a string
      if not isinstance(initialText, basestring):
        initialText = "" # replace the non-strong with an empty string
      entry.set_text(initialText)
      entry.select_region(0,-1)
      # make sure the text is visible (TODO: respect current theme, but make sure the text will be visible ?)
      entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
      entry.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse('white'))
      #allow the user to press enter to do ok
      entry.connect("activate", self.respondToTextEntry, dialog, gtk.RESPONSE_OK, instance,key, persistentKey)
      dialog.connect("response", self.respondToDialog,entry, instance,key, persistentKey)
      #create a horizontal box to pack the entry and a label
      vbox = gtk.VBox(True)
      if description:
        descLabel = gtk.Label()
        descLabel.set_markup(description)
        descLabel.set_line_wrap(True)
        descLabel.set_max_width_chars(-1)
        vbox.pack_start(descLabel, True, True, 5)
        vbox.pack_end(entry)
      else:
        vbox.pack_start(entry, False, 5, 5)
      #add it and show it
      dialog.vbox.pack_end(vbox, True, True, 0)
      self.clearEntry()
      (width, height) = dialog.get_size() # get the current size
      (x,y,w,h) = self.get('viewport')
      dialog.resize(w,height) # resize the dialog to the width of the window and leave height the same
      dialog.set_keep_above(True)
      self.dmod.textEntryIminent()
      self.entryBoxVisible = True
      dialog.show_all()

  def isEntryBoxvisible(self):
    """report if the current entry box is visible
       - so that for example the display module can distinguish
       normal minimization events and losing focus due to the modal
       text entry box"""
    return self.entryBoxVisible

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
