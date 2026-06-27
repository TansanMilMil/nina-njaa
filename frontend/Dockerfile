FROM node:20.19.2-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["cp", "-r", "/app/dist/.", "/static/"]
