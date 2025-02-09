# Use Python as base image
FROM python:3.10

# Set working directory inside the container
WORKDIR /app

# Copy requirements first for caching dependencies
COPY requirements.txt .

# Install dependencies including Uvicorn
RUN pip install --no-cache-dir -r requirements.txt uvicorn

# Copy the rest of the app files
COPY . .

# Expose port (optional, depending on deployment)
EXPOSE 8000

# Run Uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
