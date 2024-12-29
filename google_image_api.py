import requests


class GoogleImageApi:
    def __init__(self, api_key, cse_id):
        """
        Initializes the GoogleImageApi instance with API key and Custom Search Engine ID.

        :param api_key: Your Google API key
        :param cse_id: Your Google Custom Search Engine ID
        """
        self.api_key = api_key
        self.cse_id = cse_id
        self.base_url = 'https://www.googleapis.com/customsearch/v1'

    def get_image_url(self, query):
        """
        Fetches the URL of the first image from a Google image search.

        :param query: The search query (e.g., "puppies")
        :return: The URL of the first image in the search results, or None if no images are found
        """
        params = {
            'q': query,
            'cx': self.cse_id,
            'key': self.api_key,
            'searchType': 'image'
        }

        response = requests.get(self.base_url, params=params)

        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                return data['items'][0]['link']  # Return the URL of the first image
            else:
                print("No images found.")
        else:
            print(f"Error {response.status_code}: {response.text}")

        return None