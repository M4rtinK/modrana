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
Version: 0.54.8
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
%doc README.rst
%license COPYING.txt
/usr/bin/*
/usr/share/modrana
/usr/share/icons/hicolor/48x48/apps/*
/usr/share/icons/hicolor/64x64/apps/*
/usr/share/icons/hicolor/128x128/apps/*
/usr/share/icons/hicolor/256x256/apps/*
%endif

%changelog
* Tue Jul 04 2017 Martin Kolman <martin.kolman@gmail.com> - 0.54.8-1
- Fix nosetests runner (martin.kolman)
- Make map config parsing more robust (martin.kolman)
- Fix a typo in the map configuration file (martin.kolman)
- Fix search progress indicator (martin.kolman)
- Drop the "starting" prefix (martin.kolman)
- Use better variable name for the thread id (martin.kolman)
- Return thread name for synchronous search calls where applicable (martin.kolman)
- Tweaks for OSM Scout Server local search (martin.kolman)
- Fix OSM Scout Server local search provider (martin.kolman)
- Show POI search result details when POI marker is clicked (martin.kolman)
- Make it possible to assign properties when dynamically loading QML files (martin.kolman)
- Add MapTextButton (martin.kolman)
- Use the POIMarkers element to display POI search results (martin.kolman)
- Remove the marker simplification logic from the Marker element (martin.kolman)
- Make it possible to also show the bubble from the right from a marker (martin.kolman)
- Add initial POIMarkers element (martin.kolman)
- Account for DPI scaling for point menu bubble margin (martin.kolman)

* Thu Jun 29 2017 Martin Kolman <martin.kolman@gmail.com> - 0.54.7-1
- Document that -1 disables the connection timeout for a layer (martin.kolman)
- Make it possible to set per-layer connection timeout (martin.kolman)
- Turn getters and setters to properties (martin.kolman)
- Fix turn by turn worker thread startup (martin.kolman)
- Categorize thread name constants a bit (martin.kolman)
- Refactor the turn-by-turn module (martin.kolman)

* Wed Mar 29 2017 Martin Kolman <martin.kolman@gmail.com> - 0.54.6-1
- Fix Monav Server based routing (martin.kolman)
- Add fallback for json import (martin.kolman)
- Handle unneeded import in protobuf code (martin.kolman)
- Display correct routing providers in GTK GUI options (martin.kolman)
- Support multiple offline routing providers per platform (martin.kolman)
- Add a list of supported online routing providers (martin.kolman)
- Add a list of offline routing providers (martin.kolman)

* Sat Mar 25 2017 Martin Kolman <martin.kolman@gmail.com> - 0.54.5-1
- Add a release target to makefile (martin.kolman)
- Fix a typo (martin.kolman)
- Make it possible to set logging trace and tracklog opacity (martin.kolman)
- Make it possible to set route opacity (martin.kolman)
- Fix indentation (martin.kolman)

* Sun Mar 19 2017 Martin Kolman <martin.kolman@gmail.com> - 0.54.4-1
- Switch README to rst & fix formatting (martin.kolman)
- Clear on-map point menus when map is clicked (martin.kolman)
- Fix map canvas debug option not being persistent (martin.kolman)
- Make top level elements rotate correctly on Sailfish OS (martin.kolman)
- Improve the application window orientation API (martin.kolman)
- List Ubuntu Components as an experimental backend (martin.kolman)
- Fix bullet point formatting (martin.kolman)
- Merge commit '7c81795d2c27b96730c606b5c88ec880d18c5773' (martin.kolman)
- Note POI search method types (martin.kolman)
- Log PyOtherSide version during startup (martin.kolman)
- Fix layer opacity setting (martin.kolman)
- Fix map layer switching (martin.kolman)
- Log how long it took to find a route (martin.kolman)
- Fix returning of results for Monav-based offline routing (martin.kolman)
- Merge branch 'master-sort_search_results_by_distance' (martin.kolman)
- Sort search results by distance (martin.kolman)
- Accommodate QML side sorting by distance (martin.kolman)
- Use formatDistance instead of custom implementation (martin.kolman)
- Add sortable QML ListModel element variant (martin.kolman)
- Merge pull request #4 from r0kk3rz/master (martin.kolman)
- Preliminary Ubuntu Touch Support (r0kk3rz)
- Fix method markup in the docs (martin.kolman)
- Add a note about the API spec to the README (martin.kolman)
- reduce TOC depth (martin.kolman)
- Remove the Authors section (martin.kolman)
- Fix the table of contents (martin.kolman)
- Add Authors section to the API spec (martin.kolman)
- Add Universal Components API specification document (martin.kolman)
- Remove a leftover modRana reference (martin.kolman)
- Add the Tensor application to the list of Universal Component users (martin.kolman)
- Update TODO (martin.kolman)
- Fix a typo (martin.kolman)
- Highlight QML code example (martin.kolman)
- Add the TopMenu element (martin.kolman)
- Add PlatformFlickable and PlatformListView elements (martin.kolman)
- Add a Popup component (martin.kolman)
- Remove remaining modRana rWin dependencies (martin.kolman)
- Convert all variant usage to var in UC (martin.kolman)
- Fix the animate argument semantics (martin.kolman)
- Correctly report window portrait status with Controls backend (martin.kolman)
- Remove a debugging message (martin.kolman)
- Show the content of the ComboBox description property (martin.kolman)
- Add the description property for ComboBox with Controls backend (martin.kolman)

* Wed Feb 01 2017 Martin Kolman <martin.kolman@gmail.com> - 0.54.3-1
- Possible fix for no tiles being shown at startup (martin.kolman)
- Fix place search (martin.kolman)

* Tue Jan 31 2017 Martin Kolman <martin.kolman@gmail.com> - 0.54.2-1
- Rename Address search to Place search (martin.kolman)
- Merge branch 'master-osm_scout_server_routing' (martin.kolman)
- Add support for using the OSM Scout Server for routing (martin.kolman)
- Add support for converting OSM Scout Server routing result JSON to a way (martin.kolman)
- Merge branch 'master-osm_scout_server_POI_search' (martin.kolman)
- Add OSM Scout Server local search support (martin.kolman)
- Add support for OSM Scout based place search (martin.kolman)
- Automatic/user triggered changed signal differentiation (martin.kolman)

* Mon Jan 30 2017 Martin Kolman <martin.kolman@gmail.com> - 0.54.1-1
- Add support for showing GPX tracklogs (martin.kolman)
- Refactoring and cleanup (martin.kolman)
- Add getters for the Qt 5 GUI (martin.kolman)
- Some loadTracklog fixes (martin.kolman)
- Add the list_logs icon (martin.kolman)
- Use map coordinates when drawing route and logging traces (martin.kolman)
- Improve coordinate conversion functions (martin.kolman)
- Fix some typos (martin.kolman)
- Scale also POI label text size according to DPI (martin.kolman)
- Scale POI markers according to DPI (martin.kolman)
- DPI scaling for the position indicator (martin.kolman)
- Add support for map canvas redraw debugging (martin.kolman)
- Actually stop drawing the trace when logging is stopped (martin.kolman)
- Disable a debug log message (martin.kolman)
- Repaint canvas once route clear button is pressed (martin.kolman)
- Filter logging trace points before drawing (martin.kolman)
- Pause trace drawing when track recording is paused (martin.kolman)
- Refactor the loadTracklogs module a bit (martin.kolman)
- Merge branch 'master-draw_track_logging_trace' (martin.kolman)
- Add support for tracklog trace drawing (martin.kolman)
- Fix formatting of the GUI style constants dictionary (martin.kolman)
- Fixup the README a bit (martin.kolman)
- Fix layout of the Bitcoin page (martin.kolman)
- Show modRana version in page header (martin.kolman)
- Fix various high DPI issues (martin.kolman)
- Fix high DPI mode style constants (martin.kolman)
- Report screen size from QML to Python (martin.kolman)
- Fix Sailfish OS detection (martin.kolman)
- Merge branch 'master-better_tile_display' (martin.kolman)
- Fix coordinate conversion functions (martin.kolman)
- Update tiles when panning (martin.kolman)
- Fix offset computation that runs when pan ends (martin.kolman)
- Work around a bug in the Sailfish OS version of Qt5 (martin.kolman)
- Comment out the position error indicator for now (martin.kolman)
- Improved tile display in Qt 5 GUI (martin.kolman)
- Use proper tile download status indication constant (martin.kolman)

* Wed Jan 04 2017 Martin Kolman <martin.kolman@gmail.com> - 0.53.5-1
- Use a slightly lighter background for the Sailfish OS icon (martin.kolman)

* Wed Jan 04 2017 Martin Kolman <martin.kolman@gmail.com> - 0.53.4-1
- Add Sailfish OS styled icon to the Silica theme (martin.kolman)
- Use appropriately styled icons on Sailfish OS (martin.kolman)
- Run unit tests with Python 3 (martin.kolman)
- Add unit test for the MapLayers class (martin.kolman)
- Fix a typo and add a nite (martin.kolman)
- Layer timeout should be either float or None (martin.kolman)
- Merge branch 'master-move_layer_classes_to_core' (martin.kolman)
- PEP 8 & docs for map layer classes (martin.kolman)
- Move layer definition classes to core (martin.kolman)

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
