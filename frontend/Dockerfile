# Use node image to build the project
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# Copy the rest of the application
COPY . .

# Build the Vite project
RUN npm run build

# Use an official NGINX image to serve the built app
FROM nginx:alpine as runner

# Set working directory
WORKDIR /usr/share/nginx/html

# Remove default NGINX static assets
RUN rm -rf ./*

# Copy built files from the builder stage
COPY --from=builder /app/dist ./

# Copy custom NGINX configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start NGINX
CMD ["nginx", "-g", "daemon off;"]
