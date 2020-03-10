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
cmd pipenv run faust -A src.back.services.game_god:game_god -L uvloop --color -l info worker
