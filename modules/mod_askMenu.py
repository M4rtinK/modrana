# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Sample of a Rana module.
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
from modules.base_module import RanaModule


def getModule(m, d, i):
    return AskMenu(m, d, i)


class AskMenu(RanaModule):
    """A module providing yes/no question dialogs"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self.menus = None
        self.question = None
        self.yesAction = None
        self.noAction = None

    def firstTime(self):
        self.menus = self.m.get('menu', None)


    def drawMenu(self, cr, menuName, args=None):
        if menuName == 'askYesNo':
            self.drawAskYesNo(cr, self.question, self.yesAction, self.noAction)

    def drawAskYesNo(self, cr, question, yesAction, noAction):
        first = (question, 'generic', '')
        second = ('YES', 'yeslong', yesAction)
        third = ('NO', 'nolong', noAction)
        self.menus.drawThreeItemHorizontalMenu(cr, first, second, third)

    def setupAskYesNo(self, question, yesAction, noAction):
        self.question = question
        self.yesAction = yesAction
        self.noAction = noAction
        self.set('menu', 'askMenu#askYesNo')
