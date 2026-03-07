FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

COPY . /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir flask gunicorn google-genai pillow

EXPOSE 8080

CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app", "--timeout", "180"]
