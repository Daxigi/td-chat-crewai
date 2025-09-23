# Use an official Python runtime as a parent image
FROM python:3.12-slim

ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# Set the working directory in the container
WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY . .

# Expose the port the app runs on
EXPOSE 8876

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8876"]
