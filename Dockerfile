# Use an official Python image
FROM python:3.11-slim

# Install system tools your app needs (Steghide, ExifTool, Ruby, zsteg, etc.)
RUN apt-get update && \
    apt-get install -y steghide exiftool ruby ruby-dev build-essential && \
    gem install zsteg && \
    apt-get clean

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Render will map it automatically)
EXPOSE 10000

# Start Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0"]
