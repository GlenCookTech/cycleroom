# Use Python as base image
<<<<<<< HEAD
FROM python:3.11
=======
FROM python:3.13
>>>>>>> bea859356d9632741ca0cd9632c615fc28a88c7b

# Set working directory inside the container
WORKDIR /app

# Copy requirements first for caching dependencies
COPY requirements.txt .

# Install DBUS
RUN apt-get update && apt-get install -y libdbus-1-dev

# Install dependencies including Uvicorn
RUN pip install --no-cache-dir -r requirements.txt uvicorn

# Copy the rest of the app files
COPY . .

# Expose port (optional, depending on deployment)
EXPOSE 8000

# Run Uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

