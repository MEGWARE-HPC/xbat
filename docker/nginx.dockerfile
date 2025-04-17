FROM docker.io/nginx:latest

COPY ./conf/nginx.conf.in /etc/nginx/nginx.conf.in


COPY ./scripts/nginx-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 7000

ENTRYPOINT ["/entrypoint.sh"]
