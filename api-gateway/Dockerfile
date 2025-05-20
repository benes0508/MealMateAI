# api-gateway/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
# Removed --production flag to ensure all dependencies including dev dependencies are installed
RUN npm install

# Copy app source code
COPY . .

# Expose the port the app will run on
EXPOSE 4000

# Start the application
CMD ["npm", "start"]