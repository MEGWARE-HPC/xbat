FROM docker.io/almalinux:9.4

# temporary fix for conflict with openssl v3 breaking changes
ENV NODE_OPTIONS=--openssl-legacy-provider

RUN yum update -y \
    && yum install -y make gcc python3.12-devel python3.12-pip python3.12-setuptools sssd-client pam openldap-devel python-devel openssl-devel libffi-devel wget zlib-devel pigz \
    && yum clean -y all

COPY ./src/setup.py /home/
COPY ./src/backend /home/backend
COPY ./src/shared /home/shared
COPY ./src/xbatctld /home/xbatctld

WORKDIR /home/

RUN ln -fs /usr/bin/python3.12 /usr/bin/python3 && ln -fs /usr/bin/python3.12 /usr/bin/python \
    && ln -fs /usr/bin/pip3.12 /usr/bin/pip3 && ln -fs /usr/bin/pip3.12 /usr/bin/pip

RUN pip3 install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r backend/requirements.txt && pip3 install -e .

EXPOSE 7001
WORKDIR /home/backend

ENV BUILD=prod
# Disable requirement for HTTPS as connection between backend and nginx is http and each request must pass through https nginx
ENV AUTHLIB_INSECURE_TRANSPORT=1

ENTRYPOINT ["/bin/sh", "-c", "gunicorn --config config-prod.py"]