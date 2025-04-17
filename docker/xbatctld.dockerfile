FROM docker.io/almalinux:9.4

WORKDIR /home/

RUN yum update -y \
    && yum install -y python3.12-devel python3.12-pip python3.12-setuptools openssl-devel bzip2-devel openssh-clients rsync \
    && yum clean -y all

COPY ./src /home/

RUN ln -fs /usr/bin/python3.12 /usr/bin/python3 && ln -fs /usr/bin/python3.12 /usr/bin/python \
    && ln -fs /usr/bin/pip3.12 /usr/bin/pip3 && ln -fs /usr/bin/pip3.12 /usr/bin/pip

RUN pip3 install --no-cache-dir -r xbatctld/requirements.txt && pip3 install -e .

WORKDIR /home/xbatctld

EXPOSE 7002

ENV BUILD=prod

ENTRYPOINT ["/bin/sh", "-c", "python3 __init__.py"]