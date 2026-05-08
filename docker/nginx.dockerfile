FROM oven/bun:alpine AS ui-builder

WORKDIR /app

COPY ./src/ui/package.json ./src/ui/package-lock.json ./

RUN bun install

COPY ./src/ui .
COPY CHANGELOG.md ./public/CHANGELOG.md

RUN bun run generate

#############################

FROM nginx:stable-alpine-slim

COPY ./conf/nginx.conf.in /etc/nginx/nginx.conf.in
COPY --from=ui-builder /app/.output/public /usr/share/nginx/html

COPY ./scripts/nginx-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 7000

ENTRYPOINT ["/entrypoint.sh"]
