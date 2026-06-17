FROM almalinux:9.8-minimal

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_NO_CACHE=1 \
    UV_COMPILE_BYTECODE=1

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /uvx /usr/local/bin/

WORKDIR /home/

RUN sed -i 's/enabled=0/enabled=1/' /etc/yum.repos.d/almalinux-crb.repo || true \
    && microdnf -y update \
    && microdnf -y install python3.12 python3.12-setuptools openssl tar gzip bzip2 openssh-clients rsync \
    && microdnf -y clean all

COPY ./src /home/

RUN ln -fs /usr/bin/python3.12 /usr/bin/python3 \
    && ln -fs /usr/bin/python3.12 /usr/bin/python

RUN uv pip install --system -r xbatctld/requirements.txt \
    && python setup.py build_proto \
    && uv pip install --system -e .

WORKDIR /home/xbatctld

EXPOSE 8002

ENV BUILD=prod

ENTRYPOINT ["/bin/sh", "-c", "python3 __init__.py"]