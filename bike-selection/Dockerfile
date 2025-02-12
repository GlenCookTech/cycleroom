# Use an official Node.js image
FROM node:22-alpine

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the entire project
COPY . .

# Expose port 3000 for the React app
EXPOSE 3030

# Start the React app
CMD ["npm", "start"]
