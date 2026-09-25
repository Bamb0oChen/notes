FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd -u 10001 -m notes && mkdir /data && chown notes:notes /data
COPY app.py passwords.py ./
USER notes
ENV THOUGHTS_DB=/data/thoughts.sqlite3
EXPOSE 8770
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8770", "--no-access-log"]
