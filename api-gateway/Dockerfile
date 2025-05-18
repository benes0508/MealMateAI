# api-gateway/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy app source code
COPY . .

# Expose the port the app will run on
EXPOSE 4000

# Start the application
CMD ["npm", "start"]