from flask import render_template
from . import main

@main.route('/', defaults={'path': ''})
@main.route('/<path:path>')
def catch_all(path):
    return render_template('index.html')
