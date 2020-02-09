from python:3.8-buster
copy . /presidents
workdir /presidents
run chmod +x ./wait-for-it.sh
run pip install pipenv
run pipenv install --deploy --ignore-pipfile
cmd pipenv run uvicorn --host 0.0.0.0 --port 80 --reload src.back.services.bot_farm:bot_farm 
