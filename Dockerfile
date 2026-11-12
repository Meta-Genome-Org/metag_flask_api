# Use the official Python image as the parent image
FROM python:3.15-slim-trixie@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

# Apply Debian security fixes the base image doesn't include yet. CI passes
# today's date as OS_UPDATES_DATE so this layer is rebuilt at least daily.
ARG OS_UPDATES_DATE
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# 
COPY requirements.txt . 

# Install the requirements, then remove pip in the same layer: it isn't used
# at runtime, and the old copies of urllib3, msgpack and setuptools bundled
# inside it (pip/_vendor) are flagged by Trivy.
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip \
    && rm -rf /root/.cache /tmp/*

# Copy the current directory contents into the container at /app
COPY . /app

# Expose port for gunicorn
EXPOSE 5000

# Run the command to start Flask
# gthread workers so the graph's parallel X and Y requests aren't serialised
CMD ["gunicorn", "--bind=0.0.0.0:5000", "--workers=2", "--threads=4", "app:app"]


