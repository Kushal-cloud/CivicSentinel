# ── Stage 1: Build ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm ci --prefer-offline

COPY . .

# VITE_API_BASE_URL is left empty so the frontend calls relative paths (/api/…)
# which Nginx then proxies to the backend. No CORS issues.
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ── Stage 2: Serve ───────────────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runner

# Copy the built React app
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our Nginx config template (uses $PORT and $BACKEND_URL placeholders)
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Railway sets $PORT dynamically. Nginx on Railway must listen on that port.
# envsubst is called automatically by the official nginx image for files in
# /etc/nginx/templates/ — it writes the rendered config to /etc/nginx/conf.d/.
ENV PORT=80
ENV BACKEND_URL=http://localhost:8000

EXPOSE 80

# Default nginx entrypoint handles envsubst + starting nginx.

