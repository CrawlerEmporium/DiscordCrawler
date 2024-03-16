FROM python:3.9-slim-bookworm
LABEL authors="Dusk"
WORKDIR /app
COPY requirements.txt ./
RUN apt-get update && apt-get install -y git
RUN pip install -U -r requirements.txt
COPY . .
CMD ["python", "./bot.py"]