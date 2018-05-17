# -*- coding: utf-8 -*-

import os, sys
import locale
import gettext

__all__ = ["_"]

# Change this variable to your app name!
#  The translation files will be under
#  @LOCALE_DIR@/@LANGUAGE@/LC_MESSAGES/@APP_NAME@.mo
APP_NAME = "modrana"
APP_DIR = "."

# .mo files will then be located in APP_DIR/translations/mo/LANGUAGECODE/LC_MESSAGES/
LOCALE_DIR = os.path.join(APP_DIR, 'translations', 'mo')

# Now we need to choose the language. We will provide a list, and gettext
# will use the first translation available in the list
#
#  In maemo it is in the LANG environment variable
#  (on desktop is usually LANGUAGES)
DEFAULT_LANGUAGES = os.environ.get('LANG', '').split(':')
DEFAULT_LANGUAGES.append('en_US')

lc, encoding = locale.getdefaultlocale()
if lc:
    languages = [lc]
else:
    languages = ['en_US']

# Concat all languages (env + default locale),
#  and here we have the languages and location of the translations
languages.extend(DEFAULT_LANGUAGES)
mo_location = LOCALE_DIR

# Lets tell those details to gettext
#  (nothing to change here for you)
#gettext.install(True, localedir=None, unicode=1)
#
gettext.find(APP_NAME, mo_location)
#
gettext.textdomain(APP_NAME)
#
gettext.bind_textdomain_codeset(APP_NAME, "UTF-8")
#
language = gettext.translation(APP_NAME, mo_location,
                                  languages=languages,
                                  fallback=True)
# the actual translation function
_ = lambda x: language.gettext(x) if x != "" else ""