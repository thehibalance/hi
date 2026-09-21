FROM python:3.12-slim

WORKDIR /app

# The API and its data live in pipeline/. The previous version copied the repo
# root and ran ./api_server.py, which has not existed at the root since 2026-04-13.
# DATA_DIR is Path("data/scores"), relative to WORKDIR, so pipeline/data/scores
# must land at /app/data/scores.
COPY pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline/ .

ENV PYTHONUNBUFFERED=1
CMD ["sh", "-c", "python -u api_server.py --port ${PORT:-8080}"]
