# syntax=docker/dockerfile:1
# install production dependencies only
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
# npm ci uses lockfile for reproducible installs; --omit=dev excludes devDependencies
RUN npm ci --omit=dev

# lean runtime image
FROM node:20-alpine
WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app --no-create-home app

# Copy only the installed modules and app source
COPY --from=builder /app/node_modules ./node_modules
COPY app.js .
COPY views ./views
COPY package.json .

RUN chown -R app:app /app
USER app

EXPOSE 3000

# Health check calls the /health route added
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
  CMD node -e "require('http').get('http://localhost:3000/health', r => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["node", "app.js"]
