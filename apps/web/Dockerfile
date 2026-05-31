FROM node:20-alpine

WORKDIR /app

COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY apps/web /app

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
