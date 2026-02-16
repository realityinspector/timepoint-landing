FROM python:3.11-alpine
WORKDIR /app
COPY index.html favicon.svg robots.txt ./
COPY server.py .
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "server.py"]
