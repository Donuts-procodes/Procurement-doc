# syntax=docker/dockerfile:1

ARG NODE_VERSION=20-alpine
FROM node:${NODE_VERSION} AS base

WORKDIR /app

# Stage 1: Install dependencies
FROM base AS deps
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Build the frontend bundle
FROM deps AS build
COPY . .
RUN npm run build

# Stage 3: Production preview / serve stage
FROM base AS runner
ENV NODE_ENV=production

USER node

COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./

EXPOSE 5174

CMD ["npm", "run", "preview"]
