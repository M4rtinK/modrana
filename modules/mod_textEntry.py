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

def getModule(m,d,i):
  return(textEntry(m,d,i))

class textEntry(ranaModule):
  """A module for hadnling text entry."""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.entryBoxVisible = False
    

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
      if response_id == gtk.RESPONSE_ACCEPT:
        print "dialog accepted"
        self.respond(entry.get_text(), instance,key)
      else:
        print "dialog rejected"
        """the dialog was rejected so we don't
        report the input that could have been entered"""


#      self.set('textEntry', entry.get_text())
#      self.set('textEntryDone', True)
      print "text entry dialog is quiting"
      dialog.destroy()

  def respond(self, result, instance, key):
#    if self.tempUnfullscreen:
#      if display:
#        if display.fullscreen():
#          display.fullscreenToggle()
#          self.tempUnfullscreen = False
    self.dmod.textEntryDone()
    instance.handleTextEntryResult(key,result)
    self.entryBoxVisible = False

  def entryBox(self, instance,key, label="Text entry", initialText="", description=None):
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
      entry.select_region(0,-1)
      # make sure the text is visible (TODO: respect current theme, but make sure the text will be visible ?)
      entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
      entry.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse('white'))
      #allow the user to press enter to do ok
      entry.connect("activate", self.respondToTextEntry, dialog, gtk.RESPONSE_OK, instance,key)
      dialog.connect("response", self.respondToDialog,entry, instance,key)
      #create a horizontal box to pack the entry and a label
      vbox = gtk.VBox()
      if description:
        descLabel = gtk.Label()
        descLabel.set_markup(description)
        vbox.pack_start(descLabel, False, 5, 5)
        vbox.pack_end(entry)
      else:
        vbox.pack_start(entry, False, 5, 5)
      #some secondary text
#      dialog.format_secondary_markup("This will be used for <i>identification</i> purposes")
      #add it and show it
      dialog.vbox.pack_end(vbox, True, True, 0)
      self.clearEntry()
      (width, height) = dialog.get_size() # get the current size
      (x,y,w,h) = self.get('viewport')
      dialog.resize(w,height) # resize the dialog to the width of the window and leave height the same
      dialog.set_keep_above(True)
#      display = self.m.get('display', None)
#      if display:
#        if display.getFullscreenEnabled():
#          display.fullscreenToggle()
#          self.tempUnfullscreen = True
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
