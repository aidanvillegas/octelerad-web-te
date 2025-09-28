FROM node:20-alpine as build
WORKDIR /app

COPY apps/web/package*.json ./
RUN npm ci

COPY apps/web ./
RUN npm run build

FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
COPY --from=build /app ./

EXPOSE 3000

CMD ["npm", "start"]
