FROM python:3.9

# Install required packages
RUN apt-get update && \
    apt-get install -y \
    imagemagick \
    ghostscript \
    libmagickwand-dev && \
    rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy Python requirements.txt
COPY requirements.txt .

# Copy ImageMagick policy
COPY policy.xml /etc/ImageMagick-6/

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy Python script
COPY send_email.py .

# Set entrypoint to Python script
ENTRYPOINT ["python", "send_email.py"]
