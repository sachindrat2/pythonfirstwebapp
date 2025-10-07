# Use official Python image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy dependency file and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Add shell script for dynamic port selection
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Command to start the app using the shell script
CMD ["/start.sh"]