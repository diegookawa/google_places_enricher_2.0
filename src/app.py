from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv, set_key
import os

app = Flask(__name__)

load_dotenv()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        api_key = request.form.get("apiKey")
        if api_key:
            dotenv_path = '../.env'
            set_key(dotenv_path, 'KEY', api_key)
            return redirect(url_for('coordinates_definition'))
    return render_template("main_page.html")

@app.route("/coordinates_definition")
def coordinates_definition():
    api_key = os.getenv('KEY')
    return render_template("coordinates_definition.html", api_key=api_key)

if __name__ == "__main__":
    app.run()
