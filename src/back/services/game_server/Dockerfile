from nikolaik/python-nodejs:python3.8-nodejs13
copy . /presidents
workdir /presidents
run chmod +x ./wait-for-it.sh
# https://stackoverflow.com/a/55610857
run pipenv install --deploy --ignore-pipfile --dev
# copy conn.py /root/.local/share/virtualenvs/presidents--b5bDiWI/lib/python3.8/site-packages/aiokafka/conn.py
run yarn install
run yarn build
cmd pipenv run uvicorn --host 0.0.0.0 --port 8000 --reload src.back.services.game_server:game_server
