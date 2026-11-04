# Use the official Python image as the parent image
FROM python:3.11-slim-buster@sha256:c46b0ae5728c2247b99903098ade3176a58e274d9c7d2efeaaab3e0621a53935

# Set the working directory to /app
WORKDIR /app

# 
COPY requirements.txt . 

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Expose port for gunicorn
EXPOSE 5000

# Run the command to start Flask
CMD ["gunicorn", "--bind=0.0.0.0:5000", "app:app"]


