from math import ceil

import article_prompt
from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson.json_util import dumps
from flask_cors import CORS
from pymongo.server_api import ServerApi
import os
from pymongo import DESCENDING
from flask_caching import Cache

app = Flask(__name__)
cors = CORS(app)
app.config['CACHE_TYPE'] = 'SimpleCache'  # Use simple in-memory cache
app.config["CACHE_DEFAULT_TIMEOUT"] = 300
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
articles_collection = db["articles"]


@app.route('/api/news/<article>', methods=['GET'])
@cache.cached(timeout=60)
def handle_path_variable(article):

    print(f'Fetching Article {article}')

    collation = {
        "locale": "en",
        "strength": 2
    }

    article_document = articles_collection.find_one(
        {"headline": {"$regex": article, "$options": "i"},
         "version": {"$in": article_prompt.SUPPORTED_VERSIONS}},
        sort=[("version", DESCENDING)],
        collation=collation
    )

    if article_document:
        return dumps(article_document)

    try:
        response = article_prompt.extract_article(os.environ['API_KEY_GEM'], os.environ['API_KEY_GOG'],
                                                  os.environ['CSE_ID'], article, mock=False, word_limit=1000)

        if not response:
            raise Exception('No Response')

        articles_collection.insert_one(response)

        return dumps(response)

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "An error occurred while fetching or saving the article."}), 500


@app.route('/api/recent-news', methods=['GET'])
@cache.cached(timeout=15, query_string=True)
def handle_recent_news():
    try:
        # Get page and limit from query params, with defaults
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))

        # Calculate the skip value based on page number and limit
        skip = (page - 1) * limit

        # Query the articles with skip and limit for pagination
        articles_cursor = (articles_collection.find({"version": {"$in": article_prompt.SUPPORTED_VERSIONS}})
                           .sort([("_id", DESCENDING)]).skip(skip).limit(limit))

        # If valid articles are found, calculate total pages and return results
        if articles_cursor:
            total_articles = (articles_collection
                              .count_documents({"version": {"$in": article_prompt.SUPPORTED_VERSIONS}}))
            total_pages = ceil(total_articles / limit)  # Calculate total pages

            # Return articles along with total pages
            return dumps({
                'articles': articles_cursor,
                'total_pages': total_pages
            })
        else:
            return jsonify({"error": "No recent articles"}), 500

    except Exception as e:
        print(f"Error fetching articles: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/search", methods=["GET"])
def search_articles():
    query = request.args.get("q", "").strip().lower()

    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    cached_results = cache.get(query)
    if cached_results:
        return jsonify(cached_results)

    # Query MongoDB
    search_results = list(articles_collection.find({
        "$or": [
            {"topic": {"$regex": query, "$options": "i"}},
            {"headline": {"$regex": query, "$options": "i"}},
            {"author": {"$regex": query, "$options": "i"}},
            {"article_body": {"$regex": query, "$options": "i"}}
        ],
        "version": {"$in": article_prompt.SUPPORTED_VERSIONS}
    },
    ))

    # Cache the results
    cache.set(query, search_results)

    # Return the results
    return dumps(search_results)


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=5000)
    app.run()
