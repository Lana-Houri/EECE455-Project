# Use an official Python image
FROM python:3.11-slim

# Install system tools and build dependencies
RUN apt-get update && \
    apt-get install -y \
        steghide \
        exiftool \
        ruby ruby-dev \
        build-essential \
        openjdk-11-jre \
        default-jre \
        wget \
        unzip \
        git \
        autoconf automake libtool \
        make gcc && \
    gem install zsteg && \
    apt-get clean

# Install OutGuess
RUN git clone https://github.com/crorvick/outguess.git /tmp/outguess && \
    cd /tmp/outguess && \
    ./autogen.sh && \
    ./configure && \
    make && \
    make install

# Install JSteg
RUN git clone https://github.com/lukechampine/jsteg.git /tmp/jsteg && \
    cd /tmp/jsteg/cmd/jsteg && \
    go build -o /usr/local/bin/jsteg

# Install F5 (f5extract)
RUN git clone https://github.com/matthewgao/F5-steganography.git /tmp/f5 && \
    cd /tmp/f5 && \
    make && \
    cp ./f5extract /usr/local/bin/f5extract

# Install OpenStego
RUN wget https://github.com/syvaidya/opensteg/releases/download/0.8.2/openstego-0.8.2.zip -O /tmp/openstego.zip && \
    unzip /tmp/openstego.zip -d /opt/openstego && \
    chmod +x /opt/openstego/bin/openstego && \
    ln -s /opt/openstego/bin/openstego /usr/local/bin/openstego

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Streamlit
EXPOSE 10000

# Start Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0"]
