import article_prompt
from flask import Flask, jsonify
from pymongo import MongoClient
import yaml
from bson.json_util import dumps
from functools import lru_cache
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)


client = MongoClient("mongodb://localhost:27017/")
db = client["fake_news"]
collection = db["articles"]

with open('properties.yml', 'r') as file:
    properties = yaml.safe_load(file)


@app.route('/api/news/<article>', methods=['GET'])
@lru_cache(maxsize=50)
def handle_path_variable(article):

    print(f'Fetching Article {article}')

    article_document = collection.find_one({"topic": article})

    if article_document and article_prompt.is_version_valid(article_document):
        return dumps(article_document)

    try:
        response = article_prompt.extract_article(properties['gemini']['api-key'], article, mock=False, word_limit=1000)

        if not response:
            raise Exception('No Response')

        collection.insert_one(response)

        return dumps(response)

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "An error occurred while fetching or saving the article."}), 500


if __name__ == "__main__":
    app.run(debug=True)