FROM python:3.11-slim

WORKDIR /app

# Salin requirements dari folder backend lokal ke container
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh isi folder backend lokal ke container
COPY . .

# Jalankan uvicorn langsung (TIDAK lewat start.sh)
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
