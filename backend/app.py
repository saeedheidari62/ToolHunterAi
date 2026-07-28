from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "ToolHunterAI API is running"
@app.route("/search")def search():    return "Search endpoint is ready"
if __name__ == "__main__":
    app.run()
