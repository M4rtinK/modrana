%global with_sailfish 0
%global with_harbour 0

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
#BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRoot: %{_tmppath}/modrana-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires: make
BuildRequires: python3-devel

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
#%setup -q
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
#make install-sailfish DESTDIR=$RPM_BUILD_ROOT
%else
make install DESTDIR=%{buildroot}
#make install DESTDIR=$RPM_BUILD_ROOT
%endif

%clean
rm -rf %{buildroot}

#%files -f %{name}
%files
%defattr(-,root,root,-)
%doc COPYING.txt
/*
#%{buildroot}/*
#%{buildroot}

%changelog
* Wed Apr 01 2015 Martin Kolman <martin.kolman@gmail.com> - 0.52.2-1
- Initial package
