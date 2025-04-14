FROM python:3.12-slim

# Create a non-root user
RUN useradd -m appuser

# Create and set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Fix permissions
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
