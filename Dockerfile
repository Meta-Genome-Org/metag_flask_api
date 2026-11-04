# Use the official Python image as the parent image
FROM python:3.9-slim-buster@sha256:320a7a4250aba4249f458872adecf92eea88dc6abd2d76dc5c0f01cac9b53990

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


