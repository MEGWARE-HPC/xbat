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
%define BASE /usr/local/share/xbatd
%define LIB %{BASE}/lib
%define LIB64 %{BASE}/lib64
%define INCLUDE %{BASE}/include

%define BUILD_BIN %{buildroot}/usr/local/bin
%define BUILD_SHARE %{buildroot}/usr/local/share/xbatd
%define SYSTEMD %{buildroot}/etc/systemd/system
%define LOG %{buildroot}/var/log/xbatd
%define LDSOCONF %{buildroot}/etc/ld.so.conf.d

mkdir -p %{LIB} %{LIB64} %{INCLUDE}

cp metrics.json %{BASE}
cp pci_devices.sh %{BASE}

cp -a /usr/lib64/libnvidia-ml.so* %{LIB64}/
ln -sf libnvidia-ml.so.1 %{LIB64}/libnvidia-ml.so

cp -a /opt/rocm/lib/libamd_smi.so* %{LIB}/

# Clean any existing build directory
rm -rf build

cmake -B build -S . \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr/local

cmake --build build --parallel

%install
rm -rf %{buildroot}

mkdir -p \
  %{BUILD_SHARE} \
  %{BUILD_BIN} \
  %{SYSTEMD} \
  %{LOG} \
  %{LDSOCONF}

cp -r /usr/local/share/xbatd/* %{BUILD_SHARE}

DESTDIR=%{buildroot} cmake --install build

%files
%defattr(-,root,root,-)
/usr/local/bin/xbatd
/usr/local/share/xbatd
/etc/systemd/system/xbatd.service
%dir /var/log/xbatd

%post
/sbin/ldconfig || /usr/sbin/ldconfig || true
systemctl daemon-reload

%preun
if [ $1 -eq 0 ]; then
    systemctl stop xbatd.service
fi

%postun
/sbin/ldconfig || /usr/sbin/ldconfig || true
systemctl daemon-reload

if [ $1 -eq 0 ]; then
    rm -rf /var/log/xbatd
fi

%clean
rm -rf %{buildroot}

%changelog
* Wed Sep 02 2026 xbatd <xbat@megware.com> - %{VERSION}-%{RELEASE}
- Build xbatd v2.0.0
- Add Enterprise Linux 10 support