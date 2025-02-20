# Use an official Node.js image
FROM node:22-alpine

# Set the working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
RUN npm install

# Copy the rest of the application
COPY . .

# Expose port 3333
EXPOSE 3333

# Start the React app
CMD ["npm", "start"]
