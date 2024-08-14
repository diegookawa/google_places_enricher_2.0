from flask import Flask, render_template, request
from dotenv import load_dotenv, set_key
import os

app = Flask(__name__)

load_dotenv()

@app.route("/", methods=["GET", "POST"])
def home():
    api_key = None
    if request.method == "POST":
        api_key = request.form.get("apiKey")
        if api_key:
            dotenv_path = '../.env'
            set_key(dotenv_path, 'KEY', api_key)
    return render_template("main_page.html", api_key=api_key)

if __name__ == "__main__":
    app.run()
