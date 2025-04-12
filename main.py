from math import ceil
import os
import re
import unicodedata

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_caching import Cache
from pymongo import MongoClient, DESCENDING
from pymongo.server_api import ServerApi
from bson.json_util import dumps

import article_prompt

app = Flask(__name__)
cors = CORS(app)

app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app)

# MongoDB connection
uri = f'mongodb+srv://filipposbagordakis:{os.environ["DB_PASSWORD"]}@theater-book.dnfffff.mongodb.net/?retryWrites=true&w=majority&appName=Theater-Book'
client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(f"MongoDB connection error: {e}")

db = client["fake_news"]
articles_collection = db["articles"]
votes_collection = db["votes"]

# Utils
def friendly_url(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')


def unfriendly_url(friendly: str) -> str:
    return friendly.replace('-', ' ').title()


def get_votes(article_id):
    pipeline = [
        {"$match": {"article_id": article_id}},
        {"$group": {
            "_id": "$like",
            "count": {"$sum": 1}
        }}
    ]

    result = votes_collection.aggregate(pipeline)

    up_votes = 0
    down_votes = 0

    for doc in result:
        if doc["_id"] is True:
            up_votes = doc["count"]
        elif doc["_id"] is False:
            down_votes = doc["count"]

    return up_votes, down_votes


@app.route('/api/vote/article', methods=['PATCH'])
def handle_vote():
    data = request.get_json()
    if not data or 'article_id' not in data or 'like' not in data:
        return jsonify({"error": "Invalid request data"}), 400

    try:
        article_id = data['article_id']['$oid']
        like = data['like']
        voter_id = ''  # In real apps, get this from session or auth token

        existing_vote = votes_collection.find_one({"article_id": article_id, "voter_id": voter_id})

        if existing_vote:
            votes_collection.update_one({"_id": existing_vote["_id"]}, {"$set": {"like": like}})
        else:
            votes_collection.insert_one({"article_id": article_id, "voter_id": voter_id, "like": like})

        return jsonify({"success": True}), 200

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "An error occurred while updating the vote."}), 500

@app.route('/api/news/<article>', methods=['GET'])
@cache.cached(timeout=15)
def handle_path_variable(article):
    article = friendly_url(article)
    print(f'Fetching Article {article}')

    try:
        collation = {"locale": "en", "strength": 2}
        article_document = articles_collection.find_one(
            {
                "topic": {"$regex": article, "$options": "i"},
                "version": {"$in": article_prompt.SUPPORTED_VERSIONS}
            },
            sort=[("version", DESCENDING)],
            collation=collation
        )

        if article_document:
            up_votes, down_votes = get_votes(str(article_document["_id"]))
            article_document["up_votes"] = up_votes
            article_document["down_votes"] = down_votes
            return dumps(article_document)

        # Article not found, try to generate and save it
        response = article_prompt.extract_article(
            os.environ['API_KEY_GEM'],
            os.environ['API_KEY_GOG'],
            os.environ['CSE_ID'],
            article,
            unfriendly_url(article),
            mock=False,
        )

        if not response:
            raise Exception("No response from extractor")

        articles_collection.insert_one(response)
        return dumps(response)

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "An error occurred while fetching or saving the article."}), 500

@app.route('/api/recent-news', methods=['GET'])
@cache.cached(timeout=15, query_string=True)
def handle_recent_news():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        skip = (page - 1) * limit

        query = {"version": {"$in": article_prompt.SUPPORTED_VERSIONS}}
        total_articles = articles_collection.count_documents(query)
        total_pages = ceil(total_articles / limit)

        articles_cursor = articles_collection.find(query).sort("_id", DESCENDING).skip(skip).limit(limit)

        result = []
        for article in articles_cursor:
            up_votes, down_votes = get_votes(str(article["_id"]))
            article["up_votes"] = up_votes
            article["down_votes"] = down_votes
            result.append(article)

        return dumps({
            'articles': result,
            'total_pages': total_pages
        })

    except Exception as e:
        print(f"Error fetching articles: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/search", methods=["GET"])
@cache.cached(timeout=15, query_string=True)
def search_articles():
    query = request.args.get("q", "").strip().lower()

    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    try:
        search_results = list(articles_collection.find({
            "$or": [
                {"topic": {"$regex": query, "$options": "i"}},
                {"headline": {"$regex": query, "$options": "i"}},
                {"author": {"$regex": query, "$options": "i"}},
                {"article_body": {"$regex": query, "$options": "i"}}
            ],
            "version": {"$in": article_prompt.SUPPORTED_VERSIONS}
        }))
        return dumps(search_results)
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({"error": "Search failed"}), 500


# Entry
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
