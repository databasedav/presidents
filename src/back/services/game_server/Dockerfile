from python:3.8-slim
workdir /presidents
copy src/back src/back
copy Pipfile Pipfile
copy Pipfile.lock Pipfile.lock
copy --chown=1 wait-for-it.sh wait-for-it.sh
run apt update
run apt install build-essential -y
run pip install pipenv
# https://stackoverflow.com/a/55610857
run pipenv install --deploy --ignore-pipfile
cmd pipenv run uvicorn --host 0.0.0.0 --port 80 --reload src.back.services.game_server:game_server
