from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        return 'POST'
    else:
        return "<p>Hello World!</p>"

if __name__ == "__main__":
    app.run(port=8000, debug=True)