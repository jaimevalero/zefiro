FROM python:3.11-slim

WORKDIR /app

# Install required packages
RUN apt-get update && apt-get install -y \
    python3.11-venv \
    python3-pip \
    python3.11-distutils \
    curl \
    pandoc \
    texlive-latex-base \
    texlive-latex-extra \
    psutils \
    wkhtmltopdf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY meta_crew_backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY meta_crew_backend /app

CMD ["uvicorn", "src.backend_fastapi.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]