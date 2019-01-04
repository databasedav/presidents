FROM node:8.10.0-alpine
RUN adduser -D presidents
WORKDIR /home/presidents
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM python:3.7-alpine
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn
ENV FLASK_APP ./src/server/listener.py
RUN chown -R presidents:presidents ./
USER presidents
EXPOSE 5000

