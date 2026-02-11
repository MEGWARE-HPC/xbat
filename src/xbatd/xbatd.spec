# rpmbuild --target x86_64 -bb xbatd.spec


Summary: xbat daemon
Name: xbatd
Version: %{VERSION}
Release: %{RELEASE}%{?dist}
License: MIT
URL: megware.com
Packager: Nico Tippmann
BuildRoot: /root/rpmbuild/
Source0: xbatd-%{VERSION}.tar.gz
BuildRoot:	%{buildroot}
AutoReqProv: no
Requires: boost-log
Requires: sysstat
Requires: libcurl
%global debug_package %{nil}
%description
xbat daemon

%prep
%setup

%build
make clean

# directories already created during likwid installation
%define BASE /usr/local/share/xbatd/
%define LIB %{BASE}/lib
%define LIB64 %{BASE}/lib64
%define INCLUDE %{BASE}/include

%define BUILD_BIN %{buildroot}/usr/local/bin
%define BUILD_SHARE %{buildroot}/usr/local/share/xbatd
%define SYSTEMD %{buildroot}/etc/systemd/system
%define LOG %{buildroot}/var/log/xbatd/

mkdir -p %{LIB} %{LIB64} %{INCLUDE}

cp metrics.json %{BASE}
cp pci_devices.sh %{BASE}
cp -r /c-questdb-client/include/* %{INCLUDE}
cp -r /c-questdb-client/build/libquestdb_client.* %{LIB}
cp -r /usr/lib64/libnvidia-ml.* %{LIB64}
ln -s %{LIB64}/libnvidia-ml.so.1 %{LIB64}/libnvidia-ml.so
cp -r /opt/rocm/lib/libamd_smi.* %{LIB}
make -e LIB_PATH=%{LIB} LIB64_PATH=%{LIB64} INCLUDE_PATH=%{INCLUDE} -j

%install 
mkdir -p %{BUILD_SHARE} %{BUILD_BIN} %{SYSTEMD} %{LOG}
cp -r /usr/local/share/xbatd/* %{BUILD_SHARE}
make -e BIN_DESTINATION=%{BUILD_BIN} SYS_DESTINATION=%{SYSTEMD} install 

%files
/usr/local/bin/xbatd
/usr/local/share/xbatd
/etc/systemd/system/xbatd.service

%post
systemctl daemon-reload

%preun
systemctl stop xbatd.service

%postun
systemctl daemon-reload

%changelog
* Wed Feb 11 2026 dtp tom.wahrenberg@megware.com - 1.0.0-rc0
- Initial RPM build
