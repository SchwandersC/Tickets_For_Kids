# Use the Selenium Standalone Chrome image as the base.
FROM selenium/standalone-chrome:latest

# Switch to root to install Python.
USER root

# Install Python3 and pip.
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory.
WORKDIR /app

# Copy the requirements file into the container.
COPY requirements.txt /app/requirements.txt

# Install the required Python packages.
RUN pip3 install --no-cache-dir -r requirements.txt

# (Optional) Copy your .env file if you need environment variables.
COPY .env /app/.env

# Copy all project files into the container.
COPY . /app

# Expose the port that your app will use (adjust if needed).
EXPOSE 5000

# Make sure the script is executable
RUN chmod +x /app/start.sh

# Set the script as the entrypoint
ENTRYPOINT ["/app/start.sh"]