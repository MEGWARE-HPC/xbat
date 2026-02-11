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

%define BASE /usr/local/share/xbatd
%define LIB %{BASE}/lib
%define LIB64 %{BASE}/lib64
%define INCLUDE %{BASE}/include

%define BUILD_BIN %{buildroot}/usr/local/bin
%define BUILD_SHARE %{buildroot}/usr/local/share/xbatd
%define SYSTEMD %{buildroot}/etc/systemd/system
%define LOG %{buildroot}/var/log/xbatd

%build
make clean

mkdir -p %{LIB} %{LIB64} %{INCLUDE}

cp metrics.json %{BASE}/
cp pci_devices.sh %{BASE}/

cp -r /c-questdb-client/include/* %{INCLUDE}/
cp -a /c-questdb-client/build/libquestdb_client.* %{LIB}/

cp -a /usr/lib64/libnvidia-ml.* %{LIB64}/ || true
ln -sf %{LIB64}/libnvidia-ml.so.1 %{LIB64}/libnvidia-ml.so || true

if [ -f /usr/include/nvml.h ]; then
  cp -a /usr/include/nvml.h %{INCLUDE}/
elif ls /usr/local/cuda*/targets/*/include/nvml.h >/dev/null 2>&1; then
  cp -a /usr/local/cuda*/targets/*/include/nvml.h %{INCLUDE}/
elif ls /usr/local/cuda*/include/nvml.h >/dev/null 2>&1; then
  cp -a /usr/local/cuda*/include/nvml.h %{INCLUDE}/
else
  echo "WARNING: nvml.h not found. Ensure cuda-nvml-devel is installed." >&2
fi

for f in $(ls -1 /opt/rocm*/lib*/libamd_smi.so* 2>/dev/null | sort -u); do
  cp -a "$f" %{LIB}/
done

for d in $(ls -d /opt/rocm*/include/amd_smi 2>/dev/null | sort -u); do
  cp -a "$d" %{INCLUDE}/
done

if [ -f /usr/local/include/likwid.h ]; then
  cp -a /usr/local/include/likwid.h %{INCLUDE}/
elif [ -f /usr/include/likwid.h ]; then
  cp -a /usr/include/likwid.h %{INCLUDE}/
elif [ -f %{INCLUDE}/likwid.h ]; then
  :
else
  echo "WARNING: likwid.h not found. Ensure LIKWID is installed and its headers are available." >&2
fi

if ls /usr/local/lib*/liblikwid.* >/dev/null 2>&1; then
  cp -a /usr/local/lib*/liblikwid.* %{LIB}/
elif ls /usr/lib64/liblikwid.* >/dev/null 2>&1; then
  cp -a /usr/lib64/liblikwid.* %{LIB64}/
elif [ -d /usr/local/share/xbatd/lib ] && [ "%{LIB}" = "/usr/local/share/xbatd/lib" ]; then
  # already in target dir, no-op
  :
elif ls /usr/local/share/xbatd/lib/liblikwid.* >/dev/null 2>&1; then
  cp -a /usr/local/share/xbatd/lib/liblikwid.* %{LIB}/
fi

make -e \
  INCLUDE_PATH=%{INCLUDE} \
  LIB_PATH=%{LIB} \
  LIB64_PATH=%{LIB64} \
  %{?_smp_mflags}

%install
rm -rf %{buildroot}
mkdir -p %{BUILD_SHARE} %{BUILD_BIN} %{SYSTEMD} %{LOG}

cp -a %{BASE}/* %{BUILD_SHARE}/

make -e \
  BIN_DESTINATION=%{BUILD_BIN} \
  SYS_DESTINATION=%{SYSTEMD} \
  install

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
* Wed Feb 11 2026 Ziwen xbat@megware.com - %{VERSION}-%{RELEASE}
- Build xbatd