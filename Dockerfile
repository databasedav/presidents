FROM node:8.10.0-alpine
RUN adduser -D presidents
WORKDIR /home/presidents
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM python:3.7-alpine
COPY --from=0 . .
WORKDIR /home/presidents
RUN pwd
RUN ls
RUN ls venv
RUN ls venv/bin
# RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN chmod +x boot.sh
ENV FLASK_APP ./src/server/listener.py
RUN chown -R presidents:presidents ./
USER presidents
EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
