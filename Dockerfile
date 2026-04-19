FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY database.py .
COPY templates/ templates/
COPY static/ static/

# Expose port
EXPOSE 5001

# Run the application
CMD ["python", "app.py"]
