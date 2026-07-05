FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY pyproject.toml /app/pyproject.toml

ENV PYTHONPATH=/app/src
ENV WEB_HOST=0.0.0.0
ENV WEB_PORT=8000

EXPOSE 8000

CMD ["python", "src/main.py", "--platform", "web"]
