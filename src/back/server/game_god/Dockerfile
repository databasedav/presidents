from python:3.7-buster
copy . /presidents
workdir /presidents
run pip install pipenv
# https://stackoverflow.com/a/55610857
run pipenv install --deploy --ignore-pipfile --dev
cmd pipenv run uvicorn --host 0.0.0.0 --port 80 --reload src.back.server.game_god.game_god:game_god
