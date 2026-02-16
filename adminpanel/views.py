from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from ai_module.matcher import score_pair

# Mongo connection
client = MongoClient("mongodb://localhost:27017/")
db = client["lostfound_db"]

lost_col = db["lost_items"]
found_col = db["found_items"]
matches_col = db["matches"]
recovered_col = db["recovered_items"]
users_col = db["users"]

# ----------------------------
# Admin Dashboard
# ----------------------------
def admin_dashboard(request):
    total_lost = lost_col.count_documents({})
    total_found = found_col.count_documents({})
    total_matches = matches_col.count_documents({})
    total_recovered = recovered_col.count_documents({})

    context = {
        "total_lost": total_lost,
        "total_found": total_found,
        "total_matches": total_matches,
        "verified": total_recovered,
    }
    return render(request, "adminpanel/admin_dashboard.html", context)


# ----------------------------
# Lost Items
# ----------------------------
def view_lost_items(request):
    items = list(lost_col.find().sort("reported_at", -1))
    return render(request, "adminpanel/lost_items.html", {"lost_items": items})

# ----------------------------
# Found Items
# ----------------------------
# ----------------------------
# Found Items
# ----------------------------
def view_found_items(request):
    """Admin updates found item status"""
    if request.method == "POST":
        updated = False
        for item in found_col.find():
            status_key = f"status_{item['found_id']}"
            new_status = request.POST.get(status_key)
            if new_status and new_status != item.get("status"):
                found_col.update_one(
                    {"found_id": item["found_id"]},
                    {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
                )
                updated = True
                if new_status == "Returned":
                    trigger_match_for_found(item)

        if updated:
            messages.success(request, "Status updated successfully!")
        else:
            messages.info(request, "No changes were made.")
        return redirect("adminpanel:found_items")

    # GET request, just display the items (no default message)
    items = list(found_col.find().sort("reported_at", -1))
    return render(request, "adminpanel/found_items.html", {"found_items": items})

# ----------------------------
# Trigger Matching for Found Item
# ----------------------------
def trigger_match_for_found(found_item):
    """Find similar Lost Items when Found Item is marked Returned"""
    lost_items = list(lost_col.find({"status": {"$in": ["Pending", "Open", None]}}))

    for lost in lost_items:
        if not lost.get("lost_id"):
            continue

        existing = matches_col.find_one({
            "lost_id": lost["lost_id"],
            "found_id": found_item["found_id"]
        })
        if existing and existing.get("status") not in ["Wrong"]:
            continue

        score = score_pair(lost, found_item)
        if score >= 0.55:
            match_doc = {
                "lost_id": lost["lost_id"],
                "found_id": found_item["found_id"],
                "lost_name": lost.get("name"),
                "found_name": found_item.get("name"),
                "lost_user": lost.get("reported_by"),
                "found_user": found_item.get("reported_by"),
                "score": round(score, 2),
                "status": "Pending",
                "timestamp": datetime.utcnow()
            }
            matches_col.insert_one(match_doc)


# ----------------------------
# Matches List View
# ----------------------------
def matches_list(request):
    """Show matches with Pending or Correct status"""
    valid_found_ids = [f["found_id"] for f in found_col.find({"status": "Returned"})]
    matched_items = list(matches_col.find({
        "found_id": {"$in": valid_found_ids},
        "status": {"$in": ["Pending", "Correct"]}
    }).sort("timestamp", -1))

    # Convert _id to string-safe alias for Django template
    for item in matched_items:
        item["id"] = str(item["_id"])

    # Prepare dictionaries for template lookup
    lost_dict = {i["lost_id"]: i for i in lost_col.find()}
    found_dict = {i["found_id"]: i for i in found_col.find()}

    return render(request, "adminpanel/matched_items.html", {
        "matched_items": matched_items,
        "lost_items": lost_dict,
        "found_items": found_dict
    })



# ----------------------------
# Match Action via Radio Button Form
# ----------------------------
def match_action_form(request, match_id):
    try:
        mid = ObjectId(match_id)
    except:
        messages.error(request, "Invalid match ID.")
        return redirect("adminpanel:matches_list")

    match = matches_col.find_one({"_id": mid})
    if not match:
        messages.error(request, "Match not found.")
        return redirect("adminpanel:matches_list")

    if request.method == "POST":
        status = request.POST.get("status")
        lost_item = lost_col.find_one({"lost_id": match["lost_id"]})
        found_item = found_col.find_one({"found_id": match["found_id"]})
        lost_user_doc = users_col.find_one({"username": match["lost_user"]})
        lost_email = lost_user_doc.get("email") if lost_user_doc else None
        now = datetime.utcnow()

        if status == "Correct":
            # Only update status in matches and send mail
            matches_col.update_one({"_id": mid}, {"$set": {"status": "Correct"}})
            if lost_email:
                try:
                    send_mail(
                        "Item Found - Collect from Admin Block",
                        f"Dear {match['lost_user']},\n\nWe found your item '{lost_item['name']}'. "
                        f"Please collect it from Admin Block Room AJ06.\n\nThank you,\nSmart Lost & Found System",
                        settings.DEFAULT_FROM_EMAIL,
                        [lost_email]
                    )
                except:
                    pass
            messages.success(request, "Status updated to Correct and email sent.")

        elif status == "Wrong":
            matches_col.delete_one({"_id": mid})
            messages.success(request, "Status updated to Wrong and removed from matched list.")

        elif status == "Handover":
            # Move to recovered items collection
            recovered_item = {
                "lost_id": match["lost_id"],
                "lost_name": match["lost_name"],
                "lost_user": match["lost_user"],
                "found_id": match["found_id"],
                "found_name": match["found_name"],
                "found_user": match["found_user"],
                "handover_at": now
            }
            matches_col.delete_one({"_id": mid})
            recovered_col.insert_one(recovered_item)

            lost_col.update_one({"lost_id": match["lost_id"]}, {"$set": {"status": "Recovered"}})
            found_col.update_one({"found_id": match["found_id"]}, {"$set": {"status": "Handed Over"}})
            messages.success(request, "Item handed over and moved to Recovered Items.")

    return redirect("adminpanel:matches_list")


# ----------------------------
# Recovered Items View
# ----------------------------
def recovered_items(request):
    recovered = list(recovered_col.find().sort("handover_at", -1))
    return render(request, "adminpanel/recovered_items.html", {"recovered_items": recovered})


# ----------------------------
# Logout
# ----------------------------
def admin_logout(request):
    if 'admin_logged_in' in request.session:
        del request.session['admin_logged_in']
    #messages.success(request, "Logged out successfully.")
    return redirect('users:admin_login')
