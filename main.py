import article_prompt
from flask import Flask, jsonify
from pymongo import MongoClient
import yaml
from bson.json_util import dumps
from functools import lru_cache
from flask_cors import CORS
from pymongo.server_api import ServerApi
import os

app = Flask(__name__)
cors = CORS(app)

uri = f'mongodb+srv://filipposbagordakis:{os.environ["DB_PASSWORD"]}@theater-book.dnfffff.mongodb.net/?retryWrites=true&w=majority&appName=Theater-Book'
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["fake_news"]
collection = db["articles"]


@app.route('/api/news/<article>', methods=['GET'])
@lru_cache(maxsize=50)
def handle_path_variable(article):

    print(f'Fetching Article {article}')

    article_document = collection.find_one({"topic": article})

    if article_document and article_prompt.is_version_valid(article_document):
        return dumps(article_document)

    try:
        response = article_prompt.extract_article(os.environ['API_KEY_GEM'], os.environ['API_KEY_GOG'],
                                                  os.environ['CSE_ID'], article, mock=False, word_limit=1000)

        if not response:
            raise Exception('No Response')

        collection.insert_one(response)

        return dumps(response)

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "An error occurred while fetching or saving the article."}), 500


if __name__ == "__main__":
    app.run(debug=True)
