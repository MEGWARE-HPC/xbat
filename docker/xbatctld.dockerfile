FROM almalinux:9.6-minimal

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /home/

RUN sed -i 's/enabled=0/enabled=1/' /etc/yum.repos.d/almalinux-crb.repo || true \
    && microdnf -y update \
    && microdnf -y install \
    python3.12 python3.12-pip python3.12-setuptools \
    openssl bzip2 \
    openssh-clients rsync \
    && microdnf -y clean all

COPY ./src/xbatctld/requirements.txt /home/xbatctld/requirements.txt
RUN python3.12 -m pip install -r /home/xbatctld/requirements.txt

COPY ./src /home/
RUN python3.12 -m pip install --no-cache-dir -e .


WORKDIR /home/xbatctld

EXPOSE 7002

ENV BUILD=prod

ENTRYPOINT ["/bin/sh", "-c", "python3 __init__.py"]