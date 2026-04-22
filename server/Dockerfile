FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend and frontend
COPY server/ /app/
COPY *.html /app/../
COPY *.css /app/../
COPY *.js /app/../
COPY robots.txt sitemap.xml /app/../

# Run migration and start
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
