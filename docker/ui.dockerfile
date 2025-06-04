ARG NODE_VERSION=20

FROM docker.io/node:20-slim as build

# TODO use bun runtime when support for cluster mode is added
# https://bun.sh/docs/runtime/nodejs-apis#node-cluster
# https://github.com/oven-sh/bun/issues/4949
# https://github.com/Unitech/pm2/issues/5774


ARG BUN_VERSION=1.1.18

WORKDIR /build

# docker run --rm --init --ulimit memlock=-1:-1 oven/bun
RUN apt-get update && apt-get install -y curl unzip
RUN curl https://bun.sh/install | bash -s -- bun-v${BUN_VERSION}

ENV PATH="${PATH}:/root/.bun/bin"

COPY ./src/ui/bun.lockb ./src/ui/package.json ./

# install all dependencies
RUN bun install

COPY ./src/ui .
COPY CHANGELOG.md ./public/CHANGELOG.md

RUN bun run build

# remove node_modules and cache to reduce image size as we only need production dependencies
RUN rm -rf node_modules && \
    rm -rf /root/.bun/install/cache/ && \
    bun install --production

# prune unnecessary files from node_modules like TypeScript sources, markdown files, etc.
RUN curl -sf https://gobinaries.com/tj/node-prune | sh && \
    node-prune

FROM node:${NODE_VERSION}-slim as distribution

WORKDIR /app

RUN npm install -g pm2

COPY --from=build --chown=node:node /build/node_modules ./node_modules
COPY --from=build --chown=node:node /build/.output ./.output
COPY --from=build --chown=node:node /build/ecosystem.config.cjs ./ecosystem.config.cjs

USER node

EXPOSE 7003
# "interpreter" parameter fixes "PM2 error: Error: spawn node ENOENT"
# https://github.com/Unitech/pm2/issues/3648
CMD ["pm2-runtime", "--interpreter=$(whereis node)", "ecosystem.config.cjs"]