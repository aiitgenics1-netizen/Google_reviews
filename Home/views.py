import re
from django.shortcuts import render, redirect, get_object_or_404
from .services.google_reviews import scrape_reviews
from .models import Business, Review
from django.utils.dateparse import parse_datetime
from django.db.models import Count, Q
from django.http import JsonResponse

def extract_data_id(url):
    if not url:
        return None

    match = re.search(r"0x[a-f0-9]+:0x[a-f0-9]+", url.lower())
    return match.group(0) if match else None


def Home(request):

    # Message stored in session temporarily
    message = request.session.pop("message", None)
    message_type = request.session.pop("message_type", None)

    if request.method == "POST":

        url = request.POST.get("url", "").strip()

        # Empty input → ignore
        if url == "":
            return redirect("home")

        data_id = extract_data_id(url)

        if not data_id:
            request.session["message"] = "Not a valid Google Maps URL"
            request.session["message_type"] = "error"
        else:
            request.session["message"] = f"Valid URL. Data ID: {data_id}"
            request.session["message_type"] = "success"



            # ⭐ CHECK DATABASE
            business = Business.objects.filter(data_id=data_id).first()

            if business:

                print("BUSINESS ALREADY EXISTS IN DATABASE")

            else:

                print("NEW BUSINESS - SCRAPING REVIEWS")

                data = scrape_reviews(data_id)

                business_data = data["business"]
                reviews = data["reviews"]

                # Create Business
                business = Business.objects.create(
                    data_id=data_id,
                    name=business_data["name"],
                    address=business_data["address"],
                    rating=business_data["rating"],
                    total_reviews=business_data["total_reviews"]
                )

                print("BUSINESS SAVED:", business.name)

                # Save Reviews
                for r in reviews:

                    Review.objects.create(

                        business=business,

                        review_id=r["review_id"],

                        reviewer_name=r["reviewer_name"],

                        rating=r["rating"],

                        text=r["text"],

                        response=r["response"],

                        review_link=r["review_link"],

                        review_date=parse_datetime(r["review_date"])
                    )

                print("TOTAL REVIEWS SAVED:", len(reviews))

        return redirect("reviews_dashboard", business_id=business.id)

    return render(
        request,
        "Home/index.html",
        {
            "message": message,
            "message_type": message_type
        }
    )



def reviews_dashboard(request, business_id):

    business = get_object_or_404(Business, id=business_id)

    reviews = Review.objects.filter(business=business)

    # ⭐ Rating filter
    rating_filter = request.GET.get("rating")

    if rating_filter:
        reviews = reviews.filter(rating=rating_filter)

    # ⭐ Name search
    name_query = request.GET.get("names")

    matched_reviews = None

    if name_query:

        names = [n.strip() for n in name_query.split(",")]

        query = Q()

        for name in names:
            query |= Q(reviewer_name__icontains=name)

        matched_reviews = Review.objects.filter(
            business=business
        ).filter(query)

    # ⭐ Positive / Negative counts
    positive = Review.objects.filter(
        business=business,
        rating__gte=4
    ).count()

    negative = Review.objects.filter(
        business=business,
        rating__lte=3
    ).count()

    context = {
        "business": business,
        "reviews": reviews.order_by("-review_date")[:100],
        "positive": positive,
        "negative": negative,
        "matched_reviews": matched_reviews
    }

    return render(
        request,
        "Home/reviews_dashboard.html",
        context
    )




# def business_list(request):

#     query = request.GET.get("q")

#     businesses = Business.objects.all().order_by("-created_at")

#     if query:
#         businesses = businesses.filter(
#             Q(name__icontains=query) |
#             Q(address__icontains=query) |
#             Q(data_id__icontains=query)
#         )

#     return render(
#         request,
#         "Home/business_list.html",
#         {
#             "businesses": businesses,
#             "query": query
#         }
#     )


def business_list(request):

    query = request.GET.get("q", "")

    businesses = Business.objects.all().order_by("-created_at")

    if query:

        businesses = businesses.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(data_id__icontains=query)
        )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":

        data = []

        for b in businesses:
            data.append({
                "id": b.id,
                "name": b.name,
                "address": b.address,
                "rating": b.rating,
                "data_id": b.data_id
            })

        return JsonResponse({"businesses": data})

    return render(request, "Home/business_list.html", {
        "businesses": businesses
    })