# ─── Build Stage ─────────────────────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app

# Use a more reliable npm registry and increase timeout
RUN npm config set registry https://registry.npmjs.org/ && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm config set fetch-retries 5

COPY package*.json ./
RUN npm install --prefer-offline || npm install

COPY . .
RUN npm run build -- --configuration production

# ─── Run Stage ───────────────────────────────────────────────────────────────
FROM nginx:alpine
COPY --from=build /app/dist/job-board /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
