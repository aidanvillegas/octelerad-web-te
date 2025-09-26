FROM node:20-alpine as build
WORKDIR /app

COPY apps/web/package*.json ./
RUN npm ci || npm install

COPY apps/web ./
RUN npm run build || npm run build --if-present

FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production

COPY --from=build /app ./

EXPOSE 3000

CMD ["npm", "start", "-p", "3000"]
