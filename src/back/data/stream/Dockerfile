from python:3.7-buster
copy . /presidents
workdir /presidents
run pip install pipenv
# https://stackoverflow.com/a/55610857
run pipenv install --deploy --ignore-pipfile --dev
cmd pipenv run faust -A src.back.data.stream:presidents_processor worker -l info
