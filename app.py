from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/bible")
def bible():
    return render_template("bible.html")

@app.route("/message")
def message():
    return render_template("message.html")

if __name__ == "__main__":
    app.run(debug=True)