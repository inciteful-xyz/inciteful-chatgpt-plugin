FROM python:3.11-slim-buster

WORKDIR /
    
COPY requirements.txt .

RUN pip install --upgrade -r requirements.txt

ENV STATIC_FILES=static

COPY app app

WORKDIR /app

EXPOSE 8080

CMD ["python", "server.py"]