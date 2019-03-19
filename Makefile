PKGNAME=modrana
VERSION=$(shell awk '/Version:/ { print $$2 }' packaging/$(PKGNAME).spec)
RELEASE=$(shell awk '/Release:/ { print $$2 }' packaging/$(PKGNAME).spec | sed -e 's|%.*$$||g')
TAG=modrana-$(VERSION)

PYTHON2=python2
PYTHON3=python3
PYTHON=$(PYTHON2)

RSYNC=rsync

QMAKE=qmake-qt5

NOSETESTS="nosetests-3"

SOURCEDIR=modrana_source
BUILDDIR=modrana_build
EXCLUDEFILE=packaging/fedora/exclude.txt
EXCLUDESAILFISH=packaging/sailfish/exclude.txt
# lists a few additional items to exclude for Harbour packages
EXCLUDEHARBOUR=packaging/sailfish/exclude_harbour.txt

DESTDIR=/

# l10n
TRANSLATIONS_DIR = translations
TS_FILE = $(TRANSLATIONS_DIR)/modrana.ts
POT_FILE = $(TRANSLATIONS_DIR)/modrana.pot

default: all

all:
	rm -rf $(SOURCEDIR)
	rm -rf $(BUILDDIR)
	mkdir $(SOURCEDIR)
	mkdir $(BUILDDIR)
	# The following decides what will be the
	# input for the rsync targets that run on 
	# the content we copy here to the sourcedir.
	cp -r core $(SOURCEDIR)
	cp -r data $(SOURCEDIR)
	cp -r modules $(SOURCEDIR)
	cp -r run $(SOURCEDIR)
	cp -r themes $(SOURCEDIR)
	cp -r modrana.py $(SOURCEDIR)
	cp -r version.txt $(SOURCEDIR)
	# translations
	mkdir $(SOURCEDIR)/$(TRANSLATIONS_DIR)
	cp $(TRANSLATIONS_DIR)/*.qm $(SOURCEDIR)/$(TRANSLATIONS_DIR)/
	cp -r $(TRANSLATIONS_DIR)/mo $(SOURCEDIR)/$(TRANSLATIONS_DIR)/

rsync:
	# cleanup the source tree
	$(RSYNC) -ar --exclude-from $(EXCLUDEFILE) $(SOURCEDIR)/ $(BUILDDIR)

rsync-sailfish:
	# cleanup the source tree for a Sailfish OS package
	$(RSYNC) -ar --exclude-from $(EXCLUDESAILFISH) $(SOURCEDIR)/ $(BUILDDIR)

rsync-harbour:
	# first mark modrana.py as not executable as Harbour RPM validator does not like that
	chmod -x $(SOURCEDIR)/modrana.py
	# also mark the startup scripts as not executable to make the Harbour RPM validator happy
	chmod -x $(SOURCEDIR)/run/*

	# cleanup the source for a Sailfish OS Harbour package
	$(RSYNC) -ar --exclude-from $(EXCLUDESAILFISH) --exclude-from $(EXCLUDEHARBOUR) $(SOURCEDIR)/ $(BUILDDIR)

clean:
	-rm *.tar.gz
	rm -rf $(SOURCEDIR)
	rm -rf $(BUILDDIR)

bytecode-python2:
	-python2 -m compileall $(BUILDDIR)

bytecode-python3:
	-python3 -m compileall $(BUILDDIR)

install:
	-mkdir -p $(DESTDIR)/usr/share/modrana
	cp -r $(BUILDDIR)/* $(DESTDIR)/usr/share/modrana
	# install *all* available icons - just in case :)
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/48x48/apps
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/64x64/apps
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/128x128/apps
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/256x256/apps
	cp packaging/icons/modrana/48x48/modrana.png $(DESTDIR)/usr/share/icons/hicolor/48x48/apps/
	cp packaging/icons/modrana/64x64/modrana.png $(DESTDIR)/usr/share/icons/hicolor/64x64/apps/
	cp packaging/icons/modrana/128x128/modrana.png $(DESTDIR)/usr/share/icons/hicolor/128x128/apps/
	cp packaging/icons/modrana/256x256/modrana.png $(DESTDIR)/usr/share/icons/hicolor/256x256/apps/
	cp packaging/fedora/modrana-qml.png $(DESTDIR)/usr/share/icons/hicolor/64x64/apps/
	# install the desktop file
	-mkdir -p $(DESTDIR)/usr/share/applications/
	cp packaging/fedora/modrana.desktop $(DESTDIR)/usr/share/applications/
	cp packaging/fedora/modrana-qt5.desktop $(DESTDIR)/usr/share/applications/
	# install the startup scripts
	-mkdir -p $(DESTDIR)/usr/bin
	cp packaging/fedora/modrana $(DESTDIR)/usr/bin/
	cp packaging/fedora/modrana-gtk $(DESTDIR)/usr/bin/
	cp packaging/fedora/modrana-qt5 $(DESTDIR)/usr/bin/
	# install the launcher
	cp run/launcher/modrana $(DESTDIR)/usr/bin/

install-sailfish:
	-mkdir -p $(DESTDIR)/usr/share/harbour-modrana
	cp -r $(BUILDDIR)/* $(DESTDIR)/usr/share/harbour-modrana
	# install the icons
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/86x86/apps/
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/108x108/apps/
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/128x128/apps/
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/172x172/apps
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/256x256/apps/
	cp packaging/icons/modrana-sailfish/86x86/harbour-modrana.png $(DESTDIR)/usr/share/icons/hicolor/86x86/apps/
	cp packaging/icons/modrana-sailfish/108x108/harbour-modrana.png $(DESTDIR)/usr/share/icons/hicolor/108x108/apps/
	cp packaging/icons/modrana-sailfish/128x128/harbour-modrana.png $(DESTDIR)/usr/share/icons/hicolor/128x128/apps/
	cp packaging/icons/modrana-sailfish/172x172/harbour-modrana.png $(DESTDIR)/usr/share/icons/hicolor/172x172/apps/
	cp packaging/icons/modrana-sailfish/256x256/harbour-modrana.png $(DESTDIR)/usr/share/icons/hicolor/256x256/apps/
	# install the desktop file
	-mkdir -p $(DESTDIR)/usr/share/applications/
	cp packaging/sailfish/harbour-modrana.desktop $(DESTDIR)/usr/share/applications/
	# install the sailfish version of the launcher
	-mkdir -p $(DESTDIR)/usr/bin
	cp run/launcher/harbour-modrana $(DESTDIR)/usr/bin/

launcher:
	# build the generic version of the Qt5/C++ native launcher
	$(QMAKE) run/launcher/launcher.pro "PREFIX=/usr/share" -o run/launcher/Makefile
	make -C run/launcher/

launcher-sailfish:
	# build the Sailfish OS specififc version of the Qt5/C++ native launcher
	$(QMAKE) run/launcher/launcher.pro "PREFIX=/usr/share" "CONFIG+=sailfish" -o run/launcher/Makefile
	make -C run/launcher/

tag:
	git tag -a -m "Tag as $(TAG)" -f $(TAG)
	@echo "Tagged as $(TAG)"

archive:
	@rm -f ChangeLog
	@make ChangeLog
	@make VersionFile
	git archive --format=tar --prefix=$(PKGNAME)-$(VERSION)/ $(TAG) > $(PKGNAME)-$(VERSION).tar
	mkdir -p $(PKGNAME)-$(VERSION)
	cp ChangeLog $(PKGNAME)-$(VERSION)/
	cp version.txt $(PKGNAME)-$(VERSION)/
	tar -rf $(PKGNAME)-$(VERSION).tar $(PKGNAME)-$(VERSION)
	gzip -9 $(PKGNAME)-$(VERSION).tar
	rm -rf $(PKGNAME)-$(VERSION)
	@echo "The archive is in $(PKGNAME)-$(VERSION).tar.gz"

scratch: 
	# make archive from folder contents, not git
	# - this is useful for debugging packaging issues to update the tarball quickly
	# - this really includes *everything* other than top-level compressed tarballs
	@rm -f ChangeLog
	@make ChangeLog
	@make VersionFile
	mkdir -p /tmp/$(PKGNAME)-$(VERSION)
	cp -r * /tmp/$(PKGNAME)-$(VERSION)
	# prevent previous tarballs from being added
	rm -f /tmp/$(PKGNAME)-$(VERSION)/*.tar.gz
	# also exclude .git
	rm -rf /tmp/$(PKGNAME)-$(VERSION)/.git
	cp ChangeLog /tmp/$(PKGNAME)-$(VERSION)/
	cp version.txt /tmp/$(PKGNAME)-$(VERSION)/
	tar -cvf $(PKGNAME)-$(VERSION).tar -C /tmp $(PKGNAME)-$(VERSION)
	gzip -9 $(PKGNAME)-$(VERSION).tar
	rm -rf /tmp/$(PKGNAME)-$(VERSION)
	@echo "The archive is in $(PKGNAME)-$(VERSION).tar.gz"

rpmlog:
	@git log --pretty="format:- %s (%ae)" $(TAG).. |sed -e 's/@.*)/)/'
	@echo

ChangeLog:
	(GIT_DIR=.git git log > .changelog.tmp && mv .changelog.tmp ChangeLog; rm -f .changelog.tmp) || (touch ChangeLog; echo 'git directory not found: installing possibly empty changelog.' >&2)

VersionFile:
	echo $(VERSION) > version.txt

tx-pull:
	cd $(TRANSLATIONS_DIR);tx pull -a
	@make lrelease
	@make mo

tx-push: lupdate pot
	cd $(TRANSLATIONS_DIR);tx push -s

tx-all: tx-push tx-pull

lupdate:
	lupdate-qt5 modules/gui_modules/gui_qt5/qml/ -ts $(TS_FILE)

lrelease:
	lrelease-qt5 $(TRANSLATIONS_DIR)/*modrana-*.ts
pot:
	truncate -s0 $(POT_FILE)
	xgettext \
	 --output=$(POT_FILE) \
	 --language=Python \
	 --from-code=UTF-8 \
	 --join-existing \
	 --keyword=_ \
	 --add-comments=TRANSLATORS: \
	 --no-wrap \
	 core/*.py \
	 modules/*.py \
	 modules/*/*.py \

mo:
	cd $(TRANSLATIONS_DIR);./generate_mo_files.py

bumpver:
	@NEWSUBVER=$$((`echo $(VERSION) |cut -d . -f 3` + 1)) ; \
	NEWVERSION=`echo $(VERSION).$$NEWSUBVER |cut -d . -f 1,2,4` ; \
	DATELINE="* `LANG=c date "+%a %b %d %Y"` `git config user.name` <`git config user.email`> - $$NEWVERSION-1"  ; \
	cl=`grep -n %changelog packaging/modrana.spec |cut -d : -f 1` ; \
	tail --lines=+$$(($$cl + 1)) packaging/modrana.spec > speclog ; \
	(head -n $$cl packaging/modrana.spec ; echo "$$DATELINE" ; make --quiet --no-print-directory rpmlog 2>/dev/null ; echo ""; cat speclog) > packaging/modrana.spec.new ; \
	mv packaging/modrana.spec.new packaging/modrana.spec ; rm -f speclog ; \
	sed -i "s/Version: $(VERSION)/Version: $$NEWVERSION/" packaging/modrana.spec ; \

commit:
	echo "New modRana version $(VERSION)" > commit_template.txt
	git commit --template=commit_template.txt
	rm commit_template.txt

release:
	@make tx-all
	# stage all changed/added gettext files
	git add $(TRANSLATIONS_DIR)/*.pot
	git add $(TRANSLATIONS_DIR)/*.po
	git add $(TRANSLATIONS_DIR)/mo
	# stage all Qt translation files
	git add $(TRANSLATIONS_DIR)/*.ts
	git add $(TRANSLATIONS_DIR)/*.qm
	@make bumpver
	git add packaging/modrana.spec
	@make commit
	@make tag
	@make archive

.PHONY: clean install tag archive

test-in-docker:
	# run tests in a Docker container
	sudo docker build -f tests/Dockerfile.test .

test: test-python test-qml

test-python:
	# run tests for Python code
	PYTHONPATH=core/bundle $(NOSETESTS) -w tests -v

test-qml:
	# run tests for QML code
	qmltestrunner -input modules/gui_modules/gui_qt5/qml/tests/ 
