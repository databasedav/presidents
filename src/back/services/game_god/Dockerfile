from python:3.8-buster
copy . /presidents
workdir /presidents
run chmod +x ./wait-for-it.sh
run pip install pipenv
# https://stackoverflow.com/a/55610857
run pipenv install --deploy --ignore-pipfile --dev
# copy conn.py /root/.local/share/virtualenvs/presidents--b5bDiWI/lib/python3.8/site-packages/aiokafka/conn.py
cmd pipenv run faust -A src.back.services.game_god:game_god -L uvloop --color -l info worker
