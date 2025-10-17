FROM almalinux:9.6-minimal

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /home/

RUN sed -i 's/enabled=0/enabled=1/' /etc/yum.repos.d/almalinux-crb.repo || true \
    && microdnf -y update \
    && microdnf -y install python3.12 python3.12-pip python3.12-setuptools openssl tar gzip bzip2 openssh-clients rsync \
    && microdnf -y clean all

COPY ./src /home/

RUN ln -fs /usr/bin/python3.12 /usr/bin/python3 && ln -fs /usr/bin/python3.12 /usr/bin/python \
    && ln -fs /usr/bin/pip3.12 /usr/bin/pip3 && ln -fs /usr/bin/pip3.12 /usr/bin/pip

RUN pip3 install --no-cache-dir -r xbatctld/requirements.txt && pip3 install -e .

WORKDIR /home/xbatctld

EXPOSE 7002

ENV BUILD=prod

ENTRYPOINT ["/bin/sh", "-c", "python3 __init__.py"]