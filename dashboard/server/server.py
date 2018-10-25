# server.py
from flask import Flask, render_template
import json

app = Flask(__name__, static_folder="../static/dist", template_folder="../static/src")
statistics = {}
# todo: bring this data from db
statistics['count'] = 100
statistics['totag'] = 20
statistics['tagging'] = 50
statistics['tagged'] = 30

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stats")
def stats():
    if statistics['tagging'] > 0:
        statistics['tagging'] -= 1
        statistics['tagged'] += 1
    return json.dumps(statistics)

if __name__ == "__main__":
    app.run()