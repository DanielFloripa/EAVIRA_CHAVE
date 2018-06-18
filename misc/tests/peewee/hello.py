from flask import Flask
app = Flask(__name__)

@app.route("/test/")
def hello():
    return "Hello World!"

@app.route("/test2/")
def hello2():
    return "FFFFFFFFFFFFFFFFFFFFuuuuuuuuuu"


hello()
hello2()
