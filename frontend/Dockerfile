FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund

COPY . .

EXPOSE 5173

CMD ["npm", "run", "docker"]
