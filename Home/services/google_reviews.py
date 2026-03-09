import os
import time
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def scrape_reviews(data_id):

    next_page_token = None
    page = 1

    business_info = {}
    reviews_collected = []

    while True:

        params = {
            "engine": "google_maps_reviews",
            "api_key": SERPAPI_KEY,
            "data_id": data_id,
        }

        if next_page_token:
            params["next_page_token"] = next_page_token
            params["num"] = 20

        search = GoogleSearch(params)
        results = search.get_dict()

        # First page contains business info
        if page == 1:
            place_info = results.get("place_info", {})

            business_info = {
                "name": place_info.get("title"),
                "address": place_info.get("address"),
                "rating": place_info.get("rating"),
                "total_reviews": place_info.get("reviews"),
            }

        reviews = results.get("reviews", [])

        if not reviews:
            break

        for review in reviews:
            response = review.get("response")
            reviews_collected.append({

                "review_id": review.get("review_id"),

                "reviewer_name": review.get("user", {}).get("name"),

                "rating": review.get("rating"),

                "text": review.get("snippet"),

                "review_link": review.get("link"),

                "review_date": review.get("iso_date"),

                "response": response.get("snippet") if response else None
            })

        next_page_token = results.get(
            "serpapi_pagination", {}
        ).get("next_page_token")

        if not next_page_token:
            break

        page += 1
        time.sleep(2)

    return {
        "business": business_info,
        "reviews": reviews_collected
    }