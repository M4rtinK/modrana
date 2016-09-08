#!/usr/bin/python3
# -*- coding: utf-8 -*-
#    This file is part of kothic, the realtime map renderer.

#   kothic is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   kothic is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with kothic.  If not, see <http://www.gnu.org/licenses/>.

import re
import os
import logging
import six

from hashlib import md5

from copy import copy, deepcopy

from .StyleChooser import StyleChooser
from .Condition import Condition


NEEDED_KEYS = set(["width", "casing-width", "fill-color", "fill-image", "icon-image", "text", "extrude", "background-image", "background-color", "pattern-image", "shield-text", "symbol-shape"])


WHITESPACE = re.compile(r'^ \s+ ', re.S | re.X)

COMMENT = re.compile(r'^ \/\* .+? \*\/ \s* ', re.S | re.X)
CLASS = re.compile(r'^ ([\.:]:?[*\w]+) \s* ', re.S | re.X)
#NOT_CLASS = re.compile(r'^ !([\.:]\w+) \s* ', re.S | re.X)
ZOOM = re.compile(r'^ \| \s* z([\d\-]+) \s* ', re.I | re.S | re.X)
GROUP = re.compile(r'^ , \s* ', re.I | re.S | re.X)
CONDITION = re.compile(r'^ \[(.+?)\] \s* ', re.S | re.X)
OBJECT = re.compile(r'^ (\*|[\w]+) \s* ', re.S | re.X)
DECLARATION = re.compile(r'^ \{(.+?)\} \s* ', re.S | re.X)
IMPORT = re.compile(r'^@import\("(.+?)"\); \s* ', re.S | re.X)
UNKNOWN = re.compile(r'^ (\S+) \s* ', re.S | re.X)

ZOOM_MINMAX = re.compile(r'^ (\d+)\-(\d+) $', re.S | re.X)
ZOOM_MIN = re.compile(r'^ (\d+)\-      $', re.S | re.X)
ZOOM_MAX = re.compile(r'^      \-(\d+) $', re.S | re.X)
ZOOM_SINGLE = re.compile(r'^        (\d+) $', re.S | re.X)

CONDITION_TRUE = re.compile(r'^ \s* ([:\w]+) \s* [?] \s*  $', re.I | re.S | re.X)
CONDITION_invTRUE = re.compile(r'^ \s* [!] \s* ([:\w]+) \s* [?] \s*  $', re.I | re.S | re.X)
CONDITION_FALSE = re.compile(r'^ \s* ([:\w]+) \s* = \s* no  \s*  $', re.I | re.S | re.X)
CONDITION_SET = re.compile(r'^ \s* ([-:\w]+) \s* $', re.S | re.X)
CONDITION_UNSET = re.compile(r'^ \s* !([:\w]+) \s* $', re.S | re.X)
CONDITION_EQ = re.compile(r'^ \s* ([:\w]+) \s* =  \s* (.+) \s* $', re.S | re.X)
CONDITION_NE = re.compile(r'^ \s* ([:\w]+) \s* != \s* (.+) \s* $', re.S | re.X)
CONDITION_GT = re.compile(r'^ \s* ([:\w]+) \s* >  \s* (.+) \s* $', re.S | re.X)
CONDITION_GE = re.compile(r'^ \s* ([:\w]+) \s* >= \s* (.+) \s* $', re.S | re.X)
CONDITION_LT = re.compile(r'^ \s* ([:\w]+) \s* <  \s* (.+) \s* $', re.S | re.X)
CONDITION_LE = re.compile(r'^ \s* ([:\w]+) \s* <= \s* (.+) \s* $', re.S | re.X)
CONDITION_REGEX = re.compile(r'^ \s* ([:\w]+) \s* =~\/ \s* (.+) \/ \s* $', re.S | re.X)

ASSIGNMENT_EVAL = re.compile(r"^ \s* (\S+) \s* \:      \s* eval \s* \( \s* ' (.+?) ' \s* \) \s* $", re.I | re.S | re.X)
ASSIGNMENT = re.compile(r'^ \s* (\S+) \s* \:      \s*          (.+?) \s*                   $', re.S | re.X)
SET_TAG_EVAL = re.compile(r"^ \s* set \s+(\S+)\s* = \s* eval \s* \( \s* ' (.+?) ' \s* \) \s* $", re.I | re.S | re.X)
SET_TAG = re.compile(r'^ \s* set \s+(\S+)\s* = \s*          (.+?) \s*                   $', re.I | re.S | re.X)
SET_TAG_TRUE = re.compile(r'^ \s* set \s+(\S+)\s* $', re.I | re.S | re.X)
EXIT = re.compile(r'^ \s* exit \s* $', re.I | re.S | re.X)

oZOOM = 2
oGROUP = 3
oCONDITION = 4
oOBJECT = 5
oDECLARATION = 6
oSUBPART = 7

DASH = re.compile(r'\-/g')
COLOR = re.compile(r'color$/')
BOLD = re.compile(r'^bold$/i')
ITALIC = re.compile(r'^italic|oblique$/i')
UNDERLINE = re.compile(r'^underline$/i')
CAPS = re.compile(r'^uppercase$/i')
CENTER = re.compile(r'^center$/i')

HEX = re.compile(r'^#([0-9a-f]+)$/i')

class MapCSS():
    def __init__(self, minscale=0, maxscale=19):
        """
        """
        self.cache = {}
        self.cache["style"] = {}
        self.minscale = minscale
        self.maxscale = maxscale
        self.scalepair = (minscale, maxscale)
        self.choosers = []
        self.choosers_by_type = {}
        self.style_loaded = False

    def parseZoom(self, s):
        if ZOOM_MINMAX.match(s):
            return tuple([float(i) for i in ZOOM_MINMAX.match(s).groups()])
        elif ZOOM_MIN.match(s):
            return float(ZOOM_MIN.match(s).groups()[0]), self.maxscale
        elif ZOOM_MAX.match(s):
            return float(self.minscale), float(ZOOM_MAX.match(s).groups()[0])
        elif ZOOM_SINGLE.match(s):
            return float(ZOOM_SINGLE.match(s).groups()[0]), float(ZOOM_SINGLE.match(s).groups()[0])
        else:
            logging.error("unparsed zoom: %s" % s)

    def get_style(self, type, tags={}, zoom=0, scale=1, zscale=.5, cache=True):
        """
        Kothic styling API
        """
        if cache:
            shash = md5(repr(type) + repr(tags) + repr(zoom)).digest()
            if shash in self.cache["style"]:
                return deepcopy(self.cache["style"][shash])
        style = []
        for chooser in self.choosers_by_type[type]:
            style = chooser.updateStyles(style, type, tags, zoom, scale, zscale)
        style = [x for x in style if x["object-id"] != "::*"]
        st = []
        for x in style:
            for k, v in [('width', 0), ('casing-width', 0)]:
                if k in x:
                    if x[k] == v:
                        del x[k]
        st = []
        for x in style:
            if not NEEDED_KEYS.isdisjoint(x):
                st.append(x)
        style = st

        if cache:
            self.cache["style"][shash] = deepcopy(style)
        return style

    def get_style_dict(self, type, tags={}, zoom=0, scale=1, zscale=.5, olddict={}, cache=True):
        r = self.get_style(type, tags, zoom, scale, zscale, cache)
        d = olddict
        for x in r:
            if x.get('object-id', '') not in d:
                d[x.get('object-id', '')] = {}
            d[x.get('object-id', '')].update(x)
        return d

    def get_interesting_tags(self, type=None, zoom=None):
        """
        Get set of interesting tags.
        """
        tags = set()
        for chooser in self.choosers:
            tags.update(chooser.get_interesting_tags(type, zoom))
        return tags

    def get_sql_hints(self, type=None, zoom=None):
        """
        Get set of interesting tags.
        """
        hints = []
        for chooser in self.choosers:
            p = chooser.get_sql_hints(type, zoom)
            if p:
                if p[0] and p[1]:
                    hints.append(p)
        return hints

    def parse(self, css=None, clamp=True, stretch=1000, filename=None):
        """
        Parses MapCSS given as string
        """
        basepath = os.curdir
        if filename:
            basepath = os.path.dirname(filename)
        if not css:
            css = open(filename).read()
        if not self.style_loaded:
            self.choosers = []
        log = logging.getLogger('mapcss.parser')
        previous = 0  # what was the previous CSS word?
        sc = StyleChooser(self.scalepair)  # currently being assembled
        css_orig = css
        css = css.strip()
        while (css):

            # Class - :motorway, :builtup, :hover
            if CLASS.match(css):
                if previous == oDECLARATION:
                    self.choosers.append(sc)
                    sc = StyleChooser(self.scalepair)

                cond = CLASS.match(css).groups()[0]
                log.debug("class found: %s" % (cond))
                css = CLASS.sub("", css)

                sc.addCondition(Condition('eq', ("::class", cond)))
                previous = oCONDITION

            ## Not class - !.motorway, !.builtup, !:hover
            #elif NOT_CLASS.match(css):
                #if (previous == oDECLARATION):
                    #self.choosers.append(sc)
                    #sc = StyleChooser(self.scalepair)

                #cond = NOT_CLASS.match(css).groups()[0]
                #log.debug("not_class found: %s" % (cond))
                #css = NOT_CLASS.sub("", css)
                #sc.addCondition(Condition('ne', ("::class", cond)))
                #previous = oCONDITION

            # Zoom
            elif ZOOM.match(css):
                if (previous != oOBJECT & previous != oCONDITION):
                    sc.newObject()

                cond = ZOOM.match(css).groups()[0]
                log.debug("zoom found: %s" % (cond))
                css = ZOOM.sub("", css)
                sc.addZoom(self.parseZoom(cond))
                previous = oZOOM

            # Grouping - just a comma
            elif GROUP.match(css):
                css = GROUP.sub("", css)
                sc.newGroup()
                previous = oGROUP

            # Condition - [highway=primary]
            elif CONDITION.match(css):
                if previous == oDECLARATION:
                    self.choosers.append(sc)
                    sc = StyleChooser(self.scalepair)
                if (previous != oOBJECT) and (previous != oZOOM) and (previous != oCONDITION):
                    sc.newObject()
                cond = CONDITION.match(css).groups()[0]
                log.debug("condition found: %s" % (cond))
                css = CONDITION.sub("", css)
                sc.addCondition(parseCondition(cond))
                previous = oCONDITION

            # Object - way, node, relation
            elif OBJECT.match(css):
                if previous == oDECLARATION:
                    self.choosers.append(sc)
                    sc = StyleChooser(self.scalepair)
                obj = OBJECT.match(css).groups()[0]
                log.debug("object found: %s" % (obj))
                css = OBJECT.sub("", css)
                sc.newObject(obj)
                previous = oOBJECT

            # Declaration - {...}
            elif DECLARATION.match(css):
                decl = DECLARATION.match(css).groups()[0]
                log.debug("declaration found: %s" % (decl))
                sc.addStyles(parseDeclaration(decl))
                css = DECLARATION.sub("", css)
                previous = oDECLARATION

            # CSS comment
            elif COMMENT.match(css):
                log.debug("comment found")
                css = COMMENT.sub("", css)

            # @import("filename.css");
            elif IMPORT.match(css):
                log.debug("import found")
                filename = os.path.join(basepath, IMPORT.match(css).groups()[0])
                try:
                    css = IMPORT.sub("", css)
                    import_text = open(os.path.join(basepath, filename), "r").read().strip()
                    css = import_text + css
                except IOError:
                    log.warning("cannot import file %s" % filename)

            # Unknown pattern
            elif UNKNOWN.match(css):
                log.warning("unknown thing found on line %s: %s" % (six.u(css_orig[:-len(six.u(css))]).count("\n") + 1, UNKNOWN.match(css).group()))
                css = UNKNOWN.sub("", css)

            else:
                log.warning("choked on: %s" % (css))
                return

        if previous == oDECLARATION:
            self.choosers.append(sc)
            sc = StyleChooser(self.scalepair)
        try:
            if clamp:
                "clamp z-indexes, so they're tightly following integers"
                zindex = set()
                for chooser in self.choosers:
                    for stylez in chooser.styles:
                        zindex.add(float(stylez.get('z-index', 0)))
                zindex = list(zindex)
                zindex.sort()
                for chooser in self.choosers:
                    for stylez in chooser.styles:
                        if 'z-index' in stylez:
                            if stretch:
                                stylez['z-index'] = 1. * zindex.index(float(stylez.get('z-index', 0))) / len(zindex) * stretch
                            else:
                                stylez['z-index'] = zindex.index(float(stylez.get('z-index', 0)))

        except TypeError:
            pass
        for chooser in self.choosers:
            for t in chooser.compatible_types:
                if t not in self.choosers_by_type:
                    self.choosers_by_type[t] = [chooser]
                else:
                    self.choosers_by_type[t].append(chooser)


def parseCondition(s):
    log = logging.getLogger('mapcss.parser.condition')
    if CONDITION_TRUE.match(s):
        a = CONDITION_TRUE.match(s).groups()
        log.debug("condition true: %s" % (a[0]))
        return Condition('true', a)
    if CONDITION_invTRUE.match(s):
        a = CONDITION_invTRUE.match(s).groups()
        log.debug("condition invtrue: %s" % (a[0]))
        return Condition('ne', (a[0], "yes"))

    if CONDITION_FALSE.match(s):
        a = CONDITION_FALSE.match(s).groups()
        log.debug("condition false: %s" % (a[0]))
        return Condition('false', a)

    if CONDITION_SET.match(s):
        a = CONDITION_SET.match(s).groups()
        log.debug("condition set: %s" % (a))
        return Condition('set', a)

    if CONDITION_UNSET.match(s):
        a = CONDITION_UNSET.match(s).groups()
        log.debug("condition unset: %s" % (a))
        return Condition('unset', a)

    if CONDITION_NE.match(s):
        a = CONDITION_NE.match(s).groups()
        log.debug("condition NE: %s = %s" % (a[0], a[1]))
        return Condition('ne', a)

    if CONDITION_LE.match(s):
        a = CONDITION_LE.match(s).groups()
        log.debug("condition LE: %s <= %s" % (a[0], a[1]))
        return Condition('<=', a)

    if CONDITION_GE.match(s):
        a = CONDITION_GE.match(s).groups()
        log.debug("condition GE: %s >= %s" % (a[0], a[1]))
        return Condition('>=', a)

    if CONDITION_LT.match(s):
        a = CONDITION_LT.match(s).groups()
        log.debug("condition LT: %s < %s" % (a[0], a[1]))
        return Condition('<', a)

    if CONDITION_GT.match(s):
        a = CONDITION_GT.match(s).groups()
        log.debug("condition GT: %s > %s" % (a[0], a[1]))
        return Condition('>', a)

    if CONDITION_REGEX.match(s):
        a = CONDITION_REGEX.match(s).groups()
        log.debug("condition REGEX: %s = %s" % (a[0], a[1]))
        return Condition('regex', a)

    if CONDITION_EQ.match(s):
        a = CONDITION_EQ.match(s).groups()
        log.debug("condition EQ: %s = %s" % (a[0], a[1]))
        return Condition('eq', a)

    else:
        log.warning("condition UNKNOWN: %s" % (s))


def parseDeclaration(s):
    """
    Parse declaration string into list of styles
    """
    styles = []
    t = {}

    for a in s.split(';'):
        # if ((o=ASSIGNMENT_EVAL.exec(a)))   { t[o[1].replace(DASH,'_')]=new Eval(o[2]); }
        if ASSIGNMENT.match(a):
            tzz = ASSIGNMENT.match(a).groups()
            t[tzz[0]] = tzz[1].strip().strip('"')
            logging.debug("%s == %s" % (tzz[0], tzz[1]))
        else:
            logging.debug("unknown %s" % (a))
    return [t]


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    mc = MapCSS(0, 19)
