import sqlite3
from flask import Flask, request

app = Flask(__name__)

@app.route('/data', methods=['POST'])
def data():
    d = request.json
    print(d)
    return "OK"

if __name__ == "__main__":
    # Run Flask server
    app.run(host="0.0.0.0", port=8070)