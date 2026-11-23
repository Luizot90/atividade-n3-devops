FROM node:22-alpine AS dependencias
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund

FROM node:22-alpine
WORKDIR /app
COPY --from=dependencias /app/node_modules ./node_modules
COPY server.js ./
ARG VERSION=1.0
ENV NODE_ENV=production APP_VERSION=$VERSION
USER node
EXPOSE 3000
CMD ["node", "server.js"]
