import time

import article_prompt
from flask import Flask, jsonify
from pymongo import MongoClient
from bson.json_util import dumps
from functools import lru_cache
from flask_cors import CORS
from pymongo.server_api import ServerApi
import os
from pymongo import DESCENDING
from flask_caching import Cache

app = Flask(__name__)
cors = CORS(app)
app.config['CACHE_TYPE'] = 'SimpleCache'  # Use simple in-memory cache
app.config['CACHE_DEFAULT_TIMEOUT'] = 5  # Cache timeout in seconds
cache = Cache(app)

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

    article_document = collection.find_one(
        {"topic": article},
        sort=[("version", DESCENDING)]
    )
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


@app.route('/api/recent-news', methods=['GET'])
@cache.cached(timeout=5)  # Cache the result for 5 seconds
def handle_recent_news():
    articles = collection.find().sort(
        [("_id", DESCENDING)]
    ).limit(10)

    valid_articles = []

    for article_document in articles:
        if article_document and article_prompt.is_version_valid(article_document):
            valid_articles.append(article_document)

    if valid_articles:
        return dumps(valid_articles)
    else:
        return jsonify({"error": "No recent articles"}), 500


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=5000)
    app.run()
