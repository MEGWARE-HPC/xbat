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
BuildRequires: chrpath
%global debug_package %{nil}
%description
xbat daemon

%prep
%setup
# directories already created during likwid installation
%define BASE /usr/local/share/xbatd
%define LIB %{BASE}/lib
%define LIB64 %{BASE}/lib64
%define INCLUDE %{BASE}/include

%define BUILD_BIN %{buildroot}/usr/local/bin
%define BUILD_SHARE %{buildroot}/usr/local/share/xbatd
%define SYSTEMD %{buildroot}/etc/systemd/system
%define LOG %{buildroot}/var/log/xbatd
%define LDSOCONF %{buildroot}/etc/ld.so.conf.d

%build
make clean

mkdir -p %{LIB} %{LIB64} %{INCLUDE}

cp metrics.json %{BASE}/
cp pci_devices.sh %{BASE}/

cp -r /c-questdb-client/include/* %{INCLUDE}/
cp -a /c-questdb-client/build/libquestdb_client.* %{LIB}/

cp -a /usr/lib64/libnvidia-ml.* %{LIB64}/ || true
ln -sf %{LIB64}/libnvidia-ml.so.1 %{LIB64}/libnvidia-ml.so || true

for f in $(ls -1 /opt/rocm*/lib*/libamd_smi.so* 2>/dev/null | sort -u); do
  cp -a "$f" %{LIB}/
done

make %{?_smp_mflags} \
  INCLUDE_PATH=%{INCLUDE} \
  LIB_PATH=%{LIB} \
  LIB64_PATH=%{LIB64}

%install
rm -rf %{buildroot}
mkdir -p %{BUILD_SHARE} %{BUILD_BIN} %{SYSTEMD} %{LOG}

cp -a %{BASE}/* %{BUILD_SHARE}/

# clean likely likwid binaries and libraries that come with RPATH (check-rpaths from el10)
find %{BUILD_SHARE} -type f -exec readelf -d {} \; 2>/dev/null | grep -E 'RPATH|RUNPATH' || true

for f in \
  %{BUILD_SHARE}/bin/likwid-lua \
  %{BUILD_SHARE}/bin/likwid-bench \
  %{BUILD_SHARE}/lib/liblikwid.so.5.5 \
  %{BUILD_SHARE}/lib/liblikwid-hwloc.so.5.5 \
; do
  if [ -f "$f" ]; then
    chrpath -d "$f" || true
  fi
done

find %{BUILD_SHARE} -type f -exec readelf -d {} \; 2>/dev/null | grep -E 'RPATH|RUNPATH' || true

mkdir -p %{LDSOCONF}
cat > %{LDSOCONF}/xbatd.conf <<'EOF'
/usr/local/share/xbatd/lib
/usr/local/share/xbatd/lib64
EOF

make -e \
  BIN_DESTINATION=%{BUILD_BIN} \
  SYS_DESTINATION=%{SYSTEMD} \
  install

%files
/usr/local/bin/xbatd
/usr/local/share/xbatd
/etc/systemd/system/xbatd.service
/etc/ld.so.conf.d/xbatd.conf

%post
/sbin/ldconfig || /usr/sbin/ldconfig || true
systemctl daemon-reload

%preun
systemctl stop xbatd.service

%postun
/sbin/ldconfig || /usr/sbin/ldconfig || true
systemctl daemon-reload

%changelog
* Wed Feb 11 2026 xbatd xbat@megware.com - %{VERSION}-%{RELEASE}
- Build xbatd v2
