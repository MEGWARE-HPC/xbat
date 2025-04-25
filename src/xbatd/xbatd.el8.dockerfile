FROM almalinux:8.10

LABEL maintainer="NicoTippmann@MEGWARE"

RUN dnf -y update && \
    dnf -y install epel-release && \
    dnf clean all

RUN dnf install -y make gcc gcc-c++ wget perl-devel perl-Data-Dumper rpm-devel rpm-build dnf-plugins-core \
    cmake libatomic rust-toolset git boost-devel libcurl-devel openssl-devel && \
    dnf clean all

RUN mkdir -p ~/rpmbuild/BUILD ~/rpmbuild/BUILDROOT ~/rpmbuild/RPMS ~/rpmbuild/SOURCES ~/rpmbuild/SPECS ~/rpmbuild/SRPMS /usr/local/share/xbatd

# install nvml
# TODO nogpgcheck
RUN dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-rhel8.repo && \
    dnf install --nogpgcheck -y nvidia-driver nvidia-driver-NVML nvidia-driver-devel cuda-nvml-devel-12-2 && dnf clean all

# install rocm
RUN dnf install -y https://repo.radeon.com/amdgpu-install/6.3/rhel/8.10/amdgpu-install-6.3.60300-1.el8.noarch.rpm && \
    dnf install -y amd-smi-lib && \
    dnf clean all

ENV CQUESTDB_VERSION=4.0.4
# install questdb client
RUN git clone https://github.com/questdb/c-questdb-client.git && cd c-questdb-client && git checkout "$CQUESTDB_VERSION" && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build

# install LIKWID
ENV LIKWID_VERSION="v5.3.0"
RUN git clone https://github.com/RRZE-HPC/likwid.git && cd likwid && git checkout "${LIKWID_VERSION}" && \
    sed -i -e 's!PREFIX ?= /usr/local#NO SPACE!PREFIX ?= /usr/local/share/xbatd/#NO SPACE!g' config.mk && \
    sed -i -e 's!MAX_NUM_THREADS = 500!MAX_NUM_THREADS = 1024!g' config.mk \
    #&& sed -i -e 's!ACCESSMODE = accessdaemon#NO SPACE!ACCESSMODE = direct#NO SPACE!g' config.mk \
    #&& sed -i -e 's!ACCESSDAEMON = $(SBINPREFIX)/likwid-accessD#NO SPACE!ACCESSDAEMON = /usr/local/share/xbatd/sbin/likwid-accessD#NO SPACE!g' config.mk \
    && make -j $(nproc) \
    && make install

ARG VERSION
ARG RELEASE

ENV XBAT_VERSION=$VERSION
ENV XBAT_RELEASE=$RELEASE
ENV APP_NAME=xbatd-${XBAT_VERSION}

RUN echo -e "%_unpackaged_files_terminate_build      0 \n%_binaries_in_noarch_packages_terminate_build   0" > /etc/rpm/macros
RUN mkdir /root/rpmbuild/SOURCES/${APP_NAME}
COPY . /root/rpmbuild/SOURCES/${APP_NAME}
RUN cd /root/rpmbuild/SOURCES/ && tar -czvf ${APP_NAME}.tar.gz ${APP_NAME}
RUN cp /root/rpmbuild/SOURCES/${APP_NAME}/xbatd.spec /root/rpmbuild/SPECS

RUN /bin/bash -c "rpmbuild --verbose --target x86_64 --define 'VERSION $XBAT_VERSION' --define 'RELEASE $XBAT_RELEASE' -bb /root/rpmbuild/SPECS/xbatd.spec"
RUN cp /root/rpmbuild/RPMS/x86_64/xbatd* /