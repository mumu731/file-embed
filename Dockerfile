# Use the official Python image as the base image
FROM python:3.10.0-slim-buster 


# Create a working directory for the app
WORKDIR /app

# Copy the application code and requirements.txt into the container
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that the FastAPI application will run on
EXPOSE 8000

# Start the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
