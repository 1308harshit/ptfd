# Financial Dashboard Docker Image Usage

This document provides instructions on how to build and run the financial-dashboard app using the Docker image.

## Build Docker Image

From the `smw/apps/financial-dashboard` directory, run:

```bash
docker build -t financial-dashboard:latest .
```

## Run Docker Container

Run the container with port 8501 exposed:

```bash
docker run -p 8501:8501 financial-dashboard:latest
```

## Access the App

Open your browser and navigate to http://localhost:8501

## Notes

- The Streamlit app inside the container listens on all network interfaces to allow external access.
- Ensure Docker is installed and running on your machine.
