FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --omit=dev

COPY src ./src
COPY docs ./docs
COPY .env.example ./

EXPOSE 8000

CMD ["node", "src/server.js"]
