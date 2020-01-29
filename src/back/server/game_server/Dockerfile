from nikolaik/python-nodejs:python3.7-nodejs13
copy . /presidents
workdir /presidents
# https://stackoverflow.com/a/55610857
run pipenv install --deploy --ignore-pipfile --dev
run yarn install
run yarn build
cmd pipenv run uvicorn --host 0.0.0.0 --port 80 --reload src.back.server.game_server.game_server:game_server
