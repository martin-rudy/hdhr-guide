FROM python:3-alpine

WORKDIR /app
COPY hdhr-guide.py .

ENV PYTHONUNBUFFERED=1

EXPOSE 9003
CMD ["python", "-u", "./hdhr-guide.py"]
