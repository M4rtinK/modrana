# if the macros are not defined, define them equal to 0
%{!?with_sailfish: %define with_sailfish 0}
%{!?with_harbour: %define with_harbour 0}

Summary:  A flexible navigation system. 
%if 0%{with_sailfish}
%define __provides_exclude_from ^%{_datadir}/.*$
%define __requires_exclude /bin/bash|/usr/bin/env|/bin/sh
Name: harbour-modrana
Release: 1
%else
Name: modrana
Release: 1%{?dist}
%endif
Url: http://modrana.org
Version: 0.53.3
Source0: modrana-%{version}.tar.gz

License: GPLv3+
Group: Applications/Productivity
BuildArch: noarch
BuildRoot: %{_tmppath}/modrana-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires: make
BuildRequires: python3-devel
BuildRequires: rsync

%if 0%{with_sailfish}
Requires: sailfishsilica-qt5
Requires: mapplauncherd-booster-silica-qt5
Requires: pyotherside-qml-plugin-python3-qt5
Requires: libsailfishapp-launcher
Requires: qt5-qtdeclarative-import-positioning
Requires: qt5-qtpositioning
%else
Requires: pyotherside
Requires: qt5-qtlocation
# qmlscene is in the qt5-qtdeclarative package
Requires: qt5-qtdeclarative-devel
Requires: qt5-qtquickcontrols
Requires: qt5-qtsensors
# pygtk2 is needed for the GTK GUI
Requires: pygtk2
%endif

%description
ModRana is a flexible navigation system for mobile linux devices.
* support for many map layers
* POI manager
* turn-by-turn navigation with voice directions
* online amenity, Wikipedia & address search
* GPX tracklog support - both creating & visualisation
* quick, elegant and touch friendly interface
* pinch zoom support (where supported)
* global landscape and portrait support
* efficient sqlite-based tile storage
* easily configurable
* powerful command-line interface
See the project homepage at http://www.modrana.org for more information.

%prep
%setup -q -n modrana-%{version}


%build
make
%if 0%{with_sailfish}
%if 0%{with_harbour}
make rsync-harbour # run the more strinc rsync for a Harbour package
%else
make rsync-sailfish # run rsync with a Sailfish OS specific filtering
%endif
make bytecode-python3 # modRana is Python 3 only on Sailfish OS
%else
make rsync # run regular rsync
# both the GTK (Python 2) and Qt 5 (Python 3) GUIs are available on Fedora
make bytecode-python2
make bytecode-python3
%endif

%install
rm -rf %{buildroot}
%if 0%{with_sailfish}
make install-sailfish DESTDIR=%{buildroot}
%else
make install DESTDIR=%{buildroot}
%endif

%clean
rm -rf %{buildroot}

%if ! 0%{with_sailfish}
%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

%postun
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%posttrans
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
%endif

%files
%defattr(-,root,root,-)
/usr/share/applications/*

%if 0%{with_sailfish}
/usr/share/harbour-modrana
/usr/share/icons/hicolor/86x86/apps/*
/usr/share/icons/hicolor/108x108/apps/*
/usr/share/icons/hicolor/128x128/apps/*
/usr/share/icons/hicolor/256x256/apps/*
%else
%doc README.md
%license COPYING.txt
/usr/bin/*
/usr/share/modrana
/usr/share/icons/hicolor/48x48/apps/*
/usr/share/icons/hicolor/64x64/apps/*
/usr/share/icons/hicolor/128x128/apps/*
/usr/share/icons/hicolor/256x256/apps/*
%endif

%changelog
* Thu Dec 01 2016 Martin Kolman <martin.kolman@gmail.com> - 0.53.3-1
- Add OSM Scout Server layers (martin.kolman)
- Some PEP8 for gprof2dot.py (martin.kolman)
- Some PEP8 for modrana.py (martin.kolman)
- Update bundled urllib3 to 1.19 (martin.kolman)
- Change thread count options a bit (martin.kolman)
- Expose automatic thread download count in the Qt 5 GUI (martin.kolman)
- Use default thread count from constants (martin.kolman)
- Fix platform detection on Sailfish OS (martin.kolman)
- Add a more comprehensive test for the Point class (martin.kolman)
- Refactor config handling code & config handling unit tests (martin.kolman)
- Redirect all log messages to stdout when running tests (martin.kolman)
- Prevent & from breaking Pango (martin.kolman)
- Merge branch 'master' of github.com:M4rtinK/modrana (martin.kolman)
- Check if the default map and user config files are valid (martin.kolman)
- Merge pull request #137 from DerDakon/preset-OpenRailwayMap (martin.kolman)
- add OpenRailwayMap overlays (eike)
- Bump map config file revision (martin.kolman)
- Add an "overlay" suffix to the OpenFireMap label (martin.kolman)
- Merge pull request #136 from DerDakon/preset-OpenFireMap (martin.kolman)
- add OpenFireMap to map presets (kde)
- Bump map config file revision (martin.kolman)
- Remove OSM prefixes for OpenStreetMap layer names (martin.kolman)
- Update URLs for OpenTopoMap, Hike & Bike and Land/Hill Shading layers (martin.kolman)
- PEP8 for the routing module (martin.kolman)
- Show what failed when routing fails (martin.kolman)
- Initial Monav Light offline routing support (martin.kolman)
- Fix imports (martin.kolman)
- More PEP8 and a little cleanup (martin.kolman)
- Add a shutdown signal (martin.kolman)
- Add a script for pretty human readable changelog generation (martin.kolman)

* Sun Oct 11 2015 Martin Kolman <martin.kolman@gmail.com> - 0.53.2-1
- Handle no results for saved overlay configs (martin.kolman)
- Hack around Android/Qt Resource import weirdness in bundled urllib3 (martin.kolman)

* Sat Oct 10 2015 Martin Kolman <martin.kolman@gmail.com> - 0.53.1-1
- Don't instantiate tile elements until layer list is loaded (martin.kolman)
- Fix a typo (martin.kolman)
- Add Thunderforest map layers (martin.kolman)
- Handle inheritence in the 2.5 property setter implementation (martin.kolman)
- Use milliseconds for internal timeout specifications consistently (martin.kolman)
- Make sure the timeout is an integer (martin.kolman)
- Improve a docstring (martin.kolman)
- Create folder for store if it does not exist yet (martin.kolman)
- Update the bundled copy of urllib3 to 1.11 (martin.kolman)
- Cleanup the PinchMap file a bit (martin.kolman)
- Handle the unlikely case of a lookup db and store db mismatch (martin.kolman)
- Don't wrap sqlite tile lookup in str() before detection (martin.kolman)
- Improve debugging output when listing stores for a tile loading request (martin.kolman)
- Use store name not full path for discovered storage db connections (martin.kolman)
- Make it possible to enable tile storage debugging from the Qt 5 GUI (martin.kolman)
- Reword debugging message triggers for tiles (martin.kolman)
- Add a log message for enabling/disabling of tile loading debugging (martin.kolman)
- Don't sleep when shutting down modRana (martin.kolman)
- Log how long store closing at shutdown took (martin.kolman)
- Move elapsed time string generation to utils (martin.kolman)
- Add information about elapsed time to relevant tile loading debugging messages (martin.kolman)
- cleanup unused imports in storeTiles (martin.kolman)
- Add more tile loading debugging messages (martin.kolman)
- Remove old tile storage testing code (martin.kolman)
- Remove some leftover debugging messages (martin.kolman)
- Implement __repr__ for the file based and sqlite tile stores (martin.kolman)
- Use the tile-storage module for tile storage (martin.kolman)
- Initial implementation (martin.kolman)
- Add the backports folder to the Python import path (martin.kolman)
- Add 'core/tile_storage/' from commit 'b41f83a698e46700468e46b52b45266451eea368' (martin.kolman)
- Refactor the AppendOnlyWay class (martin.kolman)
- Make the polyline decoding method public and switch to underscores (martin.kolman)
- Refactor the Way class (martin.kolman)
- Refactor TurnByTurnPoint (martin.kolman)
- Forward command like arguments in startup scripts (martin.kolman)
- Fix generic pc startup script (martin.kolman)
- Add an initial ultra rudimentary unit test for the Point class (martin.kolman)
- Refactor the POI database to a separate module (martin.kolman)
- Reword the "POI added" message a bit (martin.kolman)
- Add function for parsing coordinates in the geo:latitude,longitude format (martin.kolman)
- Make it possible to get POI category by name (martin.kolman)
- Add the poi list-categories subcommand (martin.kolman)
- Add initial poi handling subcommand (martin.kolman)
- The database index might not always be an integer (martin.kolman)
- Refactor and cleanup the menu module a bit (martin.kolman)
- Display Japanese and long strings correctly in notifications (martin.kolman)
- Make it possible to measure the size of wrapped text (martin.kolman)
- Correctly display Japanese on POI markers (martin.kolman)
- Small search result drawing refactoring (martin.kolman)
- Big Point class usage cleanup and improvements (martin.kolman)
- Make it possible to send messages from the main modRana class (martin.kolman)
- Log the "no message handler" error (martin.kolman)
- Rename the check target to test target (martin.kolman)
- Small Point module/class refactoring (martin.kolman)
- Turn point lat, lon and elevation to proper properties (martin.kolman)
- Add basic unit testing infrastructure (martin.kolman)
- Use correct values when generating quad keys (martin.kolman)

* Tue Jun 16 2015 Martin Kolman <martin.kolman@gmail.com> - 0.52.10-1
- Make sure the background bubble stays visible on Sailfish OS (martin.kolman)
- Add long-click menu with a "route here" button (martin.kolman)
- Set start and destination by a function (martin.kolman)
- Add functions for enabling and disabling the routing UI (martin.kolman)
- Make it possible to set marker name when appending it (martin.kolman)
- Move the pinch and mouse areas under them tile grid (martin.kolman)
- Make pan detection HiDPI aware (martin.kolman)
- Don't trigger the long-click signal if a pan is in progress (martin.kolman)
- Clarify Python 3 support (martin.kolman)
- Round position change when panning during pinch zoom (martin.kolman)
- Refactor the map marker implementation (martin.kolman)
- Add support for long-click detection to the PinchMap element (martin.kolman)
- Use rWin.lastGoodPos when computing distance to search results (martin.kolman)

* Wed May 27 2015 Martin Kolman <martin.kolman@gmail.com> - 0.52.9-1
- Make sure that version.txt is present in sourcedir (martin.kolman)

* Mon May 25 2015 Martin Kolman <martin.kolman@gmail.com> - 0.52.8-1
- Create a version.txt file when making the tarball (martin.kolman)

* Tue May 19 2015 Martin Kolman <martin.kolman@gmail.com> - 0.52.7-1
- Only show the keep-screen-on toggle when it does something (martin.kolman)

* Sat May 16 2015 Martin Kolman <martin.kolman@gmail.com> - 0.52.6-1
- More Sailfish Harbour packaging fixes (martin.kolman)

* Wed May 13 2015 Martin Kolman <martin.kolman@gmail.com> - 0.52.5-1
- Remove python3-base dependency on Sailfish OS (martin.kolman)

* Wed May 13 2015 Martin Kolman <martin.kolman@gmail.com> - 0.52.4-1
- Sailfish packaging fixes (martin.kolman)

* Tue Apr 21 2015 Martin Kolman <martin.kolman@gmail.com> - 0.52.3-1
- Fix the Sailfish QML mangling script (martin.kolman)

* Wed Apr 01 2015 Martin Kolman <martin.kolman@gmail.com> - 0.52.2-1
- Initial package
