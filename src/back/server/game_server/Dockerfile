from python:3.7-buster
copy src/back /src/back
copy Pipfile Pipfile
copy Pipfile.lock Pipfile.lock
run pip install pipenv
# https://stackoverflow.com/a/55610857
run pipenv install --deploy --ignore-pipfile --dev
cmd pipenv run uvicorn --host 0.0.0.0 --reload src.back.server.game_server.game_server:game_server
