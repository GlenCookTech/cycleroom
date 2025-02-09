
# Use official Node.js image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY *.py .

# Expose backend port
EXPOSE 8888

# Start the server
CMD ["python", "server.py"]
