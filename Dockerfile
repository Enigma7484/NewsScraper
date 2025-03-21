# Use Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose the port Fly.io will use
EXPOSE 5001

# Command to run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "sentiment_api:app"]