FROM node:lts-alpine AS builder

WORKDIR /app

COPY ./src/ui/package.json ./src/ui/package-lock.json ./ 

RUN npm ci

COPY ./src/ui .
COPY CHANGELOG.md ./public/CHANGELOG.md

RUN npm run build

#############################

FROM node:lts-alpine AS runner

WORKDIR /app

COPY --from=builder /app/.output .output
COPY --from=builder /app/package.json .
COPY --from=builder /app/ecosystem.config.cjs .

RUN npm install -g pm2

USER node

EXPOSE 7003

CMD ["pm2-runtime", "--interpreter=node", "ecosystem.config.cjs"]