FROM almalinux:10.1-minimal

# require crb for ninja-build
RUN microdnf -y update && \
    microdnf -y install \
        epel-release \
        ca-certificates \
        git \
        wget \
        make \
        gcc gcc-c++ \
        perl-devel perl-Data-Dumper \
        rpm-devel rpm-build \
        cmake \
        libatomic \
        rust-toolset \
        boost-devel \
        libcurl-devel \
        openssl-devel && \
    microdnf -y install --enablerepo=crb \
        ninja-build \
        python3-wheel && \
    microdnf clean all

RUN mkdir -p ~/rpmbuild/BUILD ~/rpmbuild/BUILDROOT ~/rpmbuild/RPMS ~/rpmbuild/SOURCES ~/rpmbuild/SPECS ~/rpmbuild/SRPMS /usr/local/share/xbatd

# install nvml
RUN curl -fsSL -o /etc/yum.repos.d/cuda-rhel10.repo \
    https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/cuda-rhel10.repo && \
    microdnf -y install \
    nvidia-driver nvidia-driver-NVML nvidia-driver-devel cuda-nvml-devel-13-1 && \
    microdnf clean all

# install rocm
RUN printf '%s\n' \
'[ROCm-7.2]' \
'name=ROCm 7.2' \
'baseurl=https://repo.radeon.com/rocm/rhel10/7.2/main/' \
'enabled=1' \
'gpgcheck=0' \
> /etc/yum.repos.d/rocm.repo

RUN microdnf -y install amd-smi-lib && microdnf clean all

ENV CQUESTDB_VERSION=4.0.5
# install questdb client
RUN git clone --depth 1 --branch "${CQUESTDB_VERSION}" https://github.com/questdb/c-questdb-client.git && \
    cd c-questdb-client && \
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && \
    cmake --build build

# install LIKWID
ENV LIKWID_VERSION="v5.5.1"
RUN git clone --depth 1 --branch "${LIKWID_VERSION}" https://github.com/RRZE-HPC/likwid.git && \
    cd likwid && \
    sed -i -e 's!PREFIX ?= /usr/local#NO SPACE!PREFIX ?= /usr/local/share/xbatd/#NO SPACE!g' config.mk && \
    sed -i -e 's!MAX_NUM_THREADS = 512!MAX_NUM_THREADS = 1024!g' config.mk && \
    make -j "$(nproc)" && \
    make install

ARG VERSION
ARG RELEASE

ENV XBAT_VERSION=$VERSION
ENV XBAT_RELEASE=$RELEASE
ENV APP_NAME=xbatd-${XBAT_VERSION}

RUN echo -e "%_unpackaged_files_terminate_build      0 \n%_binaries_in_noarch_packages_terminate_build   0" > /etc/rpm/macros
RUN mkdir -p /root/rpmbuild/SOURCES/${APP_NAME}
COPY . /root/rpmbuild/SOURCES/${APP_NAME}
RUN cd /root/rpmbuild/SOURCES/ && tar -czvf ${APP_NAME}.tar.gz ${APP_NAME}
RUN cp /root/rpmbuild/SOURCES/${APP_NAME}/xbatd.spec /root/rpmbuild/SPECS

RUN /bin/bash -c "rpmbuild --verbose --target x86_64 --define 'VERSION $XBAT_VERSION' --define 'RELEASE $XBAT_RELEASE' -bb /root/rpmbuild/SPECS/xbatd.spec"
RUN cp /root/rpmbuild/RPMS/x86_64/xbatd* /