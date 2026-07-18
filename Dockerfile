# Use the official, lightweight Python 3.12 image
FROM python:3.12-slim

# Install uv immediately
RUN pip install uv

# Set the working directory inside the container
WORKDIR /app

# Copy the configuration files needed for installation
COPY pyproject.toml .
COPY README.md .

# Copy your application source code (including the Markdown runbooks)
COPY src/ ./src/

# Use uv to install the application and dependencies blazing fast
# --system tells uv to install globally in the container instead of making a venv
# --no-cache prevents it from saving temporary setup files to keep the image small
RUN uv pip install --system --no-cache .

# Expose the port that FastAPI will run on
EXPOSE 8000

# Command to run the Uvicorn server, bound to all network interfaces (0.0.0.0)
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]