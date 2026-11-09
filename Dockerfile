# Use the official Python image as the parent image
FROM python:3.13-slim-trixie@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90

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
CMD ["gunicorn", "--bind=0.0.0.0:5000", "app:app"]


