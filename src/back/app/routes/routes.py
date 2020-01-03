from flask import render_template, jsonify
from . import main, server_browser


@main.route("/", defaults={"path": ""})
@main.route("/<path:path>")
def catch_all(path):
    return render_template("index.html")
