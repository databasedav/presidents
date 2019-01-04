FROM nikolaik/python-nodejs:latest
RUN mkdir presidents
WORKDIR /presidents
COPY . .
RUN npm run setup
RUN npm run build
RUN chmod +x boot.sh
ENV FLASK_APP ./src/server/listener.py
# RUN chown -R presidents:presidents ./
# USER presidents
EXPOSE 5000
ENTRYPOINT ["./boot.sh"]

# FROM python:3.7-alpine

# # Install node prereqs, nodejs and yarn
# # Ref: https://deb.nodesource.com/setup_10.x
# # Ref: https://yarnpkg.com/en/docs/install
# # RUN \
# # apk update && \
# # apk add apt-transport-https
# RUN \
# echo "deb https://deb.nodesource.com/node_10.x stretch main" > /etc/apt/sources.list.d/nodesource.list && \
# wget -qO- https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
# echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list && \
# wget -qO- https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && \
# apk update && \
# apt install nodejs yarn && \
# pip install -U pip && pip install pipenv && \
# npm i -g npm@^6 && \
# rm -rf /var/lib/apt/lists/*
