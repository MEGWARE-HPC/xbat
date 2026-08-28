FROM almalinux:9.8-minimal

# temporary fix for conflict with openssl v3 breaking changes
ENV NODE_OPTIONS=--openssl-legacy-provider \
    UV_NO_CACHE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=0 \
    PATH="/home/.venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /uvx /usr/local/bin/

RUN sed -i 's/enabled=0/enabled=1/' /etc/yum.repos.d/almalinux-crb.repo || true \
    && microdnf -y update \
    && microdnf -y install make gcc python3.12 python3.12-devel python3.12-setuptools sssd-client pam openldap-devel libffi zlib wget tar gzip pigz \
    && microdnf -y clean all

RUN microdnf install -y yum-utils && \
    yum-config-manager --add-repo https://packages.clickhouse.com/rpm/clickhouse.repo && \
    microdnf install -y clickhouse-client

COPY ./src/pyproject.toml ./src/uv.lock /home/

WORKDIR /home/

RUN ln -fs /usr/bin/python3.12 /usr/bin/python3 \
    && ln -fs /usr/bin/python3.12 /usr/bin/python

RUN uv sync \
    --locked \
    --no-dev \
    --group backend \
    --no-install-project

COPY ./src/setup.py /home/
COPY ./src/backend /home/backend
COPY ./src/shared /home/shared
COPY ./src/xbatctld /home/xbatctld

RUN uv sync \
    --locked \
    --no-dev \
    --group backend \
    --no-editable

EXPOSE 8001
WORKDIR /home/backend

ENV BUILD=prod
# Disable requirement for HTTPS as connection between backend and nginx is http and each request must pass through https nginx
ENV AUTHLIB_INSECURE_TRANSPORT=1

ENTRYPOINT ["/bin/sh", "-c", "gunicorn --config config-prod.py"]