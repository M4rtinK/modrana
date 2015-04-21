# if the macros are not defined, define them equal to 0
%if 0%{!?with_sailfish}
%define with_sailfish 0
%endif

%if 0%{!?with_harbour}
%define with_harbour 0
%endif

Summary:  A flexible navigation system. 
%if 0%{with_sailfish}
Name: harbour-modrana
%else
Name: modrana
%endif
Url: http://modrana.org
Version: 0.52.2
Release: 1%{?dist}
Source0: modrana-%{version}.tar.gz

License: GPLv3+
Group: Applications/Productivity
BuildArch: noarch
BuildRoot: %{_tmppath}/modrana-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires: make
BuildRequires: python3-devel
BuildRequires: rsync

%if 0%{with_sailfish}
Requires: python3-base
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
* Wed Apr 01 2015 Martin Kolman <martin.kolman@gmail.com> - 0.52.2-1
- Initial package
