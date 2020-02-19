from python:3.8-buster
copy . /presidents
workdir /presidents
run pip install pipenv
run pipenv install --deploy --ignore-pipfile
cmd pipenv run faust -A src.back.services.monitor:monitor -L uvloop --color -l info worker
