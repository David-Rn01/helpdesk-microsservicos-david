FROM python:3.12-slim

# Não roda como root dentro do contêiner
RUN useradd --create-home --uid 10001 helpdesk

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

USER helpdesk
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
EXPOSE 8000
# O gateway é o único exposto: não confia em X-Forwarded-For vindo de fora
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
