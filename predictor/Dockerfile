FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code (model is optional - will use rule-based if not found)
COPY predictor.py .
COPY storm_classifier.pkl* ./

# Run
CMD ["python", "predictor.py"]