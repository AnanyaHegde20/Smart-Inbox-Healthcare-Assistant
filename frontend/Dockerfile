# ============================================================
# Dockerfile - Angular Frontend
# ============================================================
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies (cached layer)
COPY package.json package-lock.json* ./
RUN npm ci --ignore-scripts

# Copy application source
COPY . .

# Build Angular application
RUN npm run build -- --configuration=production

# ============================================================
# Runtime stage - Nginx
# ============================================================
FROM nginx:alpine AS runtime

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built Angular application from builder
COPY --from=builder /app/dist/frontend/browser /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup && \
    chown -R appuser:appgroup /usr/share/nginx/html && \
    chown -R appuser:appgroup /var/cache/nginx && \
    chown -R appuser:appgroup /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appgroup /var/run/nginx.pid

USER appuser

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
