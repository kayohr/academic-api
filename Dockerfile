# --- Dev stage ---
FROM node:20-alpine AS dev
WORKDIR /app

# Instala Python3 e dependências das migrations
RUN apk add --no-cache python3 py3-pip && \
    pip3 install --no-cache-dir --break-system-packages psycopg2-binary python-dotenv

COPY package*.json ./
RUN npm install
COPY . .
CMD ["node", "--watch", "src/app.js"]

# --- Build stage ---
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY . .

# --- Production stage ---
FROM node:20-alpine AS prod
WORKDIR /app
ENV NODE_ENV=production

# Python para migrations em produção
RUN apk add --no-cache python3 py3-pip && \
    pip3 install --no-cache-dir --break-system-packages psycopg2-binary python-dotenv

COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/src ./src
COPY --from=build /app/migrations ./migrations
COPY --from=build /app/package.json .
CMD ["node", "src/app.js"]
