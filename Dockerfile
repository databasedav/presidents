FROM nikolaik/python-nodejs:latest
RUN mkdir presidents
WORKDIR /presidents
COPY . .
RUN npm run setup
RUN npm run build
RUN chmod +x boot.sh
ENV FLASK_APP ./src/server/listener.py
EXPOSE 5000
CMD ["./boot.sh"]
