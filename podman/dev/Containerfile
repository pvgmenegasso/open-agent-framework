# Use the official Python image (slim version to keep it minimal)
FROM python:3.14-slim

# Set the working directory inside the container
WORKDIR /app

RUN python -m pip install pipenv

# Copy Pipfile and Pipfile.lock into the container
COPY Pipfile $BUILD_FOLDER /app/
COPY Pipfile.lock $BUILD_FOLDER /app/ 

# Install the Python dependencies defined in Pipfile
RUN python -m pipenv install --dev

# Expose the FastAPI app port
EXPOSE 8000

# Run FastAPI using Uvicorn (recommended for local development)
CMD ["pipenv", "run", "fastapi", "dev"]