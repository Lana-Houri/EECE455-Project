# Use Ubuntu base so we can install all stego tools
FROM ubuntu:22.04

# Prevent interactive prompts during install
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
        python3 python3-pip python3-venv \
        steghide \
        exiftool \
        ruby ruby-dev \
        build-essential \
        openjdk-11-jre \
        wget unzip git \
        autoconf automake libtool make gcc \
        golang-go && \
    gem install zsteg

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

# Create app directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit port
EXPOSE 10000

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0"]
