# rpmbuild --target x86_64 -bb xbatd.spec

# Disable automatic dependency detection for better control
%global _enable_debug_package 0
%global debug_package %{nil}
%global __os_install_post /usr/lib/rpm/brp-compress %{nil}

Summary: xbat daemon
Name: xbatd
Version: %{VERSION}
Release: %{RELEASE}%{?dist}
License: MIT
URL: megware.com
Packager: Nico Tippmann
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Source0: xbatd-%{VERSION}.tar.gz
AutoReqProv: no

# Build requirements
BuildRequires: cmake >= 3.12
BuildRequires: gcc-c++
BuildRequires: make

# Runtime requirements
Requires: boost-log
Requires: sysstat
Requires: libcurl

%description
xbat daemon

%prep
%setup

%build
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
# LIKWID is already installed at %{LIB} location, no need to copy

# Clean any existing build directory
rm -rf build

cmake -B build -S . \
  -DCMAKE_CXX_FLAGS="-I/opt/rocm/include -I/usr/local/cuda/include" \
  -DCMAKE_EXE_LINKER_FLAGS="-L/opt/rocm/lib -L/usr/lib64 -L%{LIB} -L%{LIB64}" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr/local

cmake --build build --parallel %{?_smp_mflags}

%install 
mkdir -p %{BUILD_SHARE} %{BUILD_BIN} %{SYSTEMD} %{LOG}
cp -r /usr/local/share/xbatd/* %{BUILD_SHARE}

DESTDIR=%{buildroot} cmake --install build 

%files
%defattr(-,root,root,-)
/usr/local/bin/xbatd
/usr/local/share/xbatd
/etc/systemd/system/xbatd.service
%dir /var/log/xbatd

%post
systemctl daemon-reload
systemctl enable xbatd.service

%preun
if [ $1 -eq 0 ]; then
    systemctl stop xbatd.service
    systemctl disable xbatd.service
fi

%postun
systemctl daemon-reload
if [ $1 -eq 0 ]; then
    rm -rf /var/log/xbatd
fi

%clean
rm -rf %{buildroot}