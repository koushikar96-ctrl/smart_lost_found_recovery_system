from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from pymongo import MongoClient, ReturnDocument
from datetime import datetime
import os

# ---------------------------
# MongoDB Setup
# ---------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["lostfound_db"]

users_collection = db["users"]
lost_items_collection = db["lost_items"]
found_items_collection = db["found_items"]
counters_collection = db["counters"]

# ---------------------------
# Helper: Auto Increment ID
# ---------------------------
def get_next_sequence(name):
    doc = counters_collection.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(doc["seq"])

# ---------------------------
# Main Item Handling View
# ---------------------------
def items_home(request):
    """
    Handles Lost & Found submissions:
    - Inserts record into MongoDB
    - Auto ID creation
    - Sends confirmation email
    - Shows success messages
    """
    username = request.session.get("username")
    if not username:
        messages.error(request, "Please log in first.")
        return redirect("users:login")

    user = users_collection.find_one({"username": username})
    user_email = user.get("email") if user else None

    if request.method == "POST":
        item_type = request.POST.get("action")  # 'lost' or 'found'
        name = request.POST.get("name", "").strip()
        category = request.POST.get("category", "").strip()
        location = request.POST.get("location", "").strip()
        description = request.POST.get("description", "").strip()
        image = request.FILES.get("image")

        # ---------------------------
        # Validation
        # ---------------------------
        if not name or not category or not location:
            messages.error(request, "Please fill all required fields (Name, Category, Location).")
            return render(request, "items/items.html", {"username": username})

        # ---------------------------
        # Save image if uploaded
        # ---------------------------
        image_name = None
        if image:
            upload_dir = os.path.join(settings.MEDIA_ROOT, "item_images")
            os.makedirs(upload_dir, exist_ok=True)
            image_path = os.path.join(upload_dir, image.name)

            with open(image_path, "wb+") as f:
                for chunk in image.chunks():
                    f.write(chunk)
            image_name = f"item_images/{image.name}"

        # ---------------------------
        # Prepare common document
        # ---------------------------
        item_doc = {
            "name": name,
            "category": category,
            "location": location,
            "description": description,
            "reported_by": username,
            "reported_at": datetime.utcnow(),
            "image": image_name,
        }

        # ---------------------------
        # LOST ITEM Handling
        # ---------------------------
        if item_type == "lost":
            lost_id = get_next_sequence("lost_id")
            item_doc["lost_id"] = lost_id
            item_doc["status"] = "Pending"

            lost_items_collection.insert_one(item_doc)

            users_collection.update_one(
                {"username": username},
                {"$inc": {"lost_count": 1}},
                upsert=True
            )

            # Email sending
            if user_email:
                try:
                    send_mail(
                        subject="Lost Item Report Confirmation - Smart Lost & Found",
                        message=(
                            f"Dear {username},\n\n"
                            f"Your lost item has been successfully recorded.\n\n"
                            f"Item Details:\n"
                            f"Name: {name}\nCategory: {category}\nLocation: {location}\n"
                            f"Description: {description}\n\n"
                            f"Lost Item ID: LST-{lost_id}\n\n"
                            f"We’ll notify you once a match is found.\n\n"
                            f"Regards,\nSmart Lost & Found Team"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user_email],
                        fail_silently=False,
                    )
                except Exception as e:
                    messages.warning(request, f"Item recorded but email failed: {e}")

            messages.success(request, f"Lost item reported successfully! (ID: LST-{lost_id})")

        # ---------------------------
        # FOUND ITEM Handling
        # ---------------------------
        elif item_type == "found":
            found_id = get_next_sequence("found_id")
            item_doc["found_id"] = found_id
            item_doc["status"] = "Pending Verification"

            found_items_collection.insert_one(item_doc)

            users_collection.update_one(
                {"username": username},
                {"$inc": {"found_count": 1}},
                upsert=True
            )

            # Email sending
            if user_email:
                try:
                    send_mail(
                        subject="Found Item Report Confirmation - Smart Lost & Found",
                        message=(
                            f"Dear {username},\n\n"
                            f"Thank you for reporting a found item.\n\n"
                            f"Item Details:\n"
                            f"Name: {name}\nCategory: {category}\nLocation: {location}\n"
                            f"Description: {description}\n\n"
                            f"Found Item ID: FND-{found_id}\n\n"
                            f"Please hand over this item at the Main Block (AJ Block, Room AJ06).\n\n"
                            f"Regards,\nSmart Lost & Found Team"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user_email],
                        fail_silently=False,
                    )
                except Exception as e:
                    messages.warning(request, f"Item recorded but email failed: {e}")

            messages.success(request, f"Found item submitted successfully! (ID: FND-{found_id})")

        # ---------------------------
        # Invalid Form Handling
        # ---------------------------
        else:
            messages.error(request, "Invalid submission type. Please try again.")

        # ---------------------------
        # Return back with message
        # ---------------------------
        return redirect("items:items_home")

    # ---------------------------
    # Render Items Page
    # ---------------------------
    return render(request, "items/items.html", {"username": username})
