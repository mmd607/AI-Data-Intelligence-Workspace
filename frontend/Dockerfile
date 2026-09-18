# syntax=docker/dockerfile:1

# Multi-stage build: compile the Vite/React SPA to static assets, then serve them with a
# minimal non-root nginx image — no Node.js, no dev server, in the final image.

FROM node:20-slim AS builder

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite inlines VITE_* variables into the built JS at build time (there is no server-side
# runtime to read them from later), so the backend URL must be supplied as a build arg.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build


FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime

COPY --from=builder /build/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# nginxinc/nginx-unprivileged already runs as a non-root user and listens on 8080.
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1:8080/ || exit 1
