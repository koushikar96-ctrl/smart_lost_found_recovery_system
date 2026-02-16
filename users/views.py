from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from pymongo import MongoClient
import random
import hashlib
from bson import ObjectId

# ------------------ MongoDB Setup ------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["lostfound_db"]

from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from pymongo import MongoClient, ReturnDocument
from datetime import datetime

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["lostfound_db"]

users_collection = db["users"]
lost_items_collection = db["lost_items"]
found_items_collection = db["found_items"]
counters_collection = db["counters"]
matched_collection = db["matched_items"]
recovered_collection = db["recovered_items"]
admins_col = db["admins"]

def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        admin = admins_col.find_one({"username": username, "password": password})
        if admin:
            request.session["admin_username"] = username
            #messages.success(request, f"Welcome {username}!")
            return redirect("adminpanel:dashboard")  # ✅ Redirect to admin dashboard
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "users/admin_login.html")


def admin_logout(request):
    request.session.pop("admin_logged_in", None)
    messages.success(request, "Admin logged out successfully.")
    return redirect("users:admin_login")

def admin_dashboard(request):
    if not request.session.get("admin_logged_in"):
        return redirect("users:admin_login")
    return render(request, "users/admin_dashboard.html")

# ----------------------------
# Lost Items Page
# ----------------------------
def admin_lost_items(request):
    if not request.session.get("admin_logged_in"):
        return redirect("users:admin_login")
    lost_items = list(lost_items_collection.find())
    return render(request, "users/admin_lost_items.html", {"lost_items": lost_items})

# ----------------------------
# Found Items Page
# ----------------------------
def admin_found_items(request):
    if not request.session.get("admin_logged_in"):
        return redirect("users:admin_login")

    if request.method == "POST":
        found_id = int(request.POST.get("found_id"))
        new_status = request.POST.get("status")  # pending or returned
        found_items_collection.update_one(
            {"found_id": found_id},
            {"$set": {"status": new_status}}
        )
        messages.success(request, f"Found item {found_id} status updated to {new_status}.")

    found_items = list(found_items_collection.find())
    return render(request, "users/admin_found_items.html", {"found_items": found_items})

# ----------------------------
# Matched Items Page
# ----------------------------
def admin_matched_items(request):
    if not request.session.get("admin_logged_in"):
        return redirect("users:admin_login")

    # Step 1: generate matches automatically
    lost_items = list(lost_items_collection.find({"status": "Pending"}))
    found_items = list(found_items_collection.find({"status": {"$in": ["Pending", "Returned"]}}))

    # Basic matching on name, category, location, description
    for lost in lost_items:
        for found in found_items:
            if (
                lost["name"].lower() == found["name"].lower() and
                lost["category"].lower() == found["category"].lower() and
                lost["location"].lower() == found["location"].lower() and
                lost["description"].lower() == found["description"].lower()
            ):
                # Check if already in matched collection
                existing = matched_collection.find_one({
                    "lost_id": lost["lost_id"],
                    "found_id": found["found_id"]
                })
                if not existing:
                    matched_collection.insert_one({
                        "lost_id": lost["lost_id"],
                        "lost_name": lost["name"],
                        "lost_user": lost["reported_by"],
                        "found_id": found["found_id"],
                        "found_name": found["name"],
                        "found_user": found["reported_by"],
                        "status": "Pending",  # Verified / Wrong / Handover
                        "created_at": datetime.utcnow()
                    })

    # Step 2: Handle admin status updates
    if request.method == "POST" and "update_status" in request.POST:
        match_id = request.POST.get("match_id")
        new_status = request.POST.get("status")  # Verified / Wrong / Handover
        match = matched_collection.find_one({"_id": match_id})
        if match:
            # Update status
            matched_collection.update_one({"_id": match_id}, {"$set": {"status": new_status}})

            # Send email if verified and found item returned
            found_item = found_items_collection.find_one({"found_id": match["found_id"]})
            if new_status == "Verified" and found_item.get("status") == "Returned":
                user_email = users_collection.find_one({"username": match["lost_user"]}).get("email")
                if user_email:
                    send_mail(
                        subject="Your Lost Item has been Found - Smart Lost & Found",
                        message=(
                            f"Dear {match['lost_user']},\n\n"
                            f"Your lost item '{match['lost_name']}' has been found.\n"
                            f"Please collect it from AJ Block, Room AJ06.\n\n"
                            f"Regards,\nSmart Lost & Found Team"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user_email],
                        fail_silently=True
                    )

            # If status is Handover → move to recovered collection
            if new_status == "Handover":
                recovered_collection.insert_one(match)
                matched_collection.delete_one({"_id": match_id})

                # Increment matched item count for both users
                users_collection.update_one({"username": match["lost_user"]}, {"$inc": {"matched_count": 1}})
                users_collection.update_one({"username": match["found_user"]}, {"$inc": {"matched_count": 1}})

            # If status is Wrong → remove from matched
            if new_status == "Wrong":
                matched_collection.delete_one({"_id": match_id})

        messages.success(request, "Match status updated successfully.")

    matched_items = list(matched_collection.find())
    return render(request, "users/admin_matched_items.html", {"matched_items": matched_items})

# ----------------------------
# Recovered Items Page
# ----------------------------
def admin_recovered_items(request):
    if not request.session.get("admin_logged_in"):
        return redirect("users:admin_login")

    recovered_items = list(recovered_collection.find())
    return render(request, "users/admin_recovered_items.html", {"recovered_items": recovered_items})

# Temporary OTP storage
otp_storage = {}

# ------------------ Home / Info ------------------
def home(request):
    return render(request, "users/home.html")

def about(request):
    return render(request, "users/home.html", {"content_title": "About Us", "content_text": """
1. User registers or logs in.
2. User uploads lost/found item info.
3. System matches items using AI.
4. User gets notification.
"""})

def contact(request):
    return render(request, "users/home.html", {"content_title": "Contact", "content_text": """
For any help, contact us:
Email: lostandfounditem25@gmail.com
Phone: +91 1234567892
"""})

def faq(request):
    return render(request, "users/home.html", {"content_title": "FAQ", "content_text": """
Q: How to report a lost item?
A: Click 'Add Lost Item' and fill the details.
Q: How do I get notifications?
A: Make sure your email/phone is verified.
"""})

# ------------------ Signup ------------------
def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        phone = request.POST['phone']
        password = request.POST['password']

        if users_collection.find_one({"username": username}):
            messages.error(request, "Username already exists.")
            return redirect('users:signup')
        if users_collection.find_one({"email": email}):
            messages.error(request, "Email already registered.")
            return redirect('users:signup')

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        users_collection.insert_one({
            "username": username,
            "email": email,
            "password": hashed_password,
            "phone": phone,
            "is_verified": False,
            "lost_count": 0,
            "found_count": 0,
            "matched_count": 0
        })

        otp = str(random.randint(10000, 99999))
        otp_storage[email] = otp
        request.session['signup_email'] = email

        send_mail(
            subject="Lost & Found Account Verification OTP",
            message=f"Your OTP is {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )

        messages.success(request, "Account created! Verify your email now.")
        return redirect('users:verify_signup_otp')

    return render(request, 'users/signup.html')

# ------------------ Verify OTP for Signup ------------------
def verify_signup_otp(request):
    email = request.session.get('signup_email')
    otp = otp_storage.get(email)

    if request.method == "POST":
        entered_otp = "".join([request.POST.get(f"otp{i}", "") for i in range(1,6)])
        if entered_otp == otp:
            users_collection.update_one({"email": email}, {"$set": {"is_verified": True}})
            otp_storage.pop(email)
            messages.success(request, "Email verified! You can now login.")
            request.session.pop('signup_email', None)
            return redirect('users:login')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "users/verify_signup_otp.html")

# ------------------ User Login ------------------
# users/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["lostfound_db"]
users_col = db["users"]
admins_col = db["admins"]

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Check Admin (unchanged)
        admin = admins_col.find_one({"username": username, "password": password})
        if admin:
            request.session["admin_logged_in"] = True
            request.session["admin_username"] = username
            #messages.success(request, f"Welcome Admin {username}!")
            return redirect("adminpanel:dashboard")

        # Check User (with hashed password validation)
        user = users_col.find_one({"username": username})
        if user:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if hashed_password == user["password"]:
                request.session["user_logged_in"] = True
                request.session["username"] = username
                #messages.success(request, f"Welcome {username}!")
                return redirect("users:user_dashboard")
            else:
                messages.error(request, "Invalid password.")
                return redirect("users:login")

        messages.error(request, "Invalid username or password.")
        return redirect("users:login")

    return render(request, "users/login.html")

# ------------------ Forgot Password ------------------
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = users_collection.find_one({"email": email})
        if not user:
            messages.error(request, "Email not registered.")
            return redirect('users:forgot_password')

        otp = str(random.randint(10000, 99999))
        otp_storage[email] = otp
        request.session['reset_email'] = email

        send_mail(
            subject="Password Reset OTP",
            message=f"Your OTP is {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )

        messages.success(request, f"OTP sent to {email}")
        return redirect("users:verify_reset_otp")

    return render(request, "users/forgot_password.html")

# ------------------ Verify OTP for Reset ------------------
def verify_reset_otp(request):
    email = request.session.get('reset_email')
    otp = otp_storage.get(email)

    if request.method == "POST":
        entered_otp = "".join([request.POST.get(f"otp{i}", "") for i in range(1,6)])
        if entered_otp == otp:
            otp_storage.pop(email)
            messages.success(request, "OTP verified. Set new password.")
            return redirect("users:set_new_password")
        else:
            messages.error(request, "Invalid OTP. Try again.")

    return render(request, "users/verify_reset_otp.html")

# ------------------ Set New Password ------------------
def set_new_password(request):
    email = request.session.get('reset_email')
    if request.method == "POST":
        new_pass = request.POST.get("new_password")
        confirm_pass = request.POST.get("confirm_password")
        if new_pass != confirm_pass:
            messages.error(request, "Passwords do not match")
            return redirect('users:set_new_password')

        hashed_password = hashlib.sha256(new_pass.encode()).hexdigest()
        users_collection.update_one(
            {"email": email},
            {"$set": {"password": hashed_password, "is_verified": True}}
        )
        request.session.pop('reset_email', None)
        messages.success(request, "Password changed successfully! You can login now.")
        return redirect("users:login")

    return render(request, "users/set_new_password.html")

# ------------------ Verify Account ------------------
def verify_account(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = users_collection.find_one({"username": username, "password": password})
        if not user:
            messages.error(request, "Invalid username or password.")
            return redirect("users:verify_account")
        if user.get("is_verified", False):
            messages.info(request, "Account already verified. Please login.")
            return redirect("users:login")

        email = user["email"]
        otp = str(random.randint(10000, 99999))
        otp_storage[email] = otp
        request.session['signup_email'] = email

        send_mail(
            subject="Lost & Found Account Verification OTP",
            message=f"Your OTP is {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )

        messages.success(request, f"OTP sent to {email}")
        return redirect("users:verify_signup_otp")

    return render(request, "users/verify_account.html")

# ------------------ Logout ------------------
def logout_user(request):
    request.session.flush()
    return redirect("users:home")

# ------------------ User Dashboard ------------------
def user_dashboard(request):
    username = request.session.get("username")
    if not username:
        messages.error(request, "Please log in first.")
        return redirect("users:login")

    user = users_collection.find_one({"username": username})
    if not user:
        messages.error(request, "User not found. Please log in again.")
        return redirect("users:login")

    context = {"username": user.get("username", "")}
    return render(request, "users/user_dashboard.html", context)

# ------------------ User Profile ------------------
def user_profile(request):
    username = request.session.get("username")
    if not username:
        messages.error(request, "Please log in first.")
        return redirect("users:login")

    user = users_collection.find_one({"username": username})
    if not user:
        messages.error(request, "User not found.")
        return redirect("users:login")

    context = {
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "lost_count": user.get("lost_count", 0),
        "found_count": user.get("found_count", 0),
        "matched_count": user.get("matched_count", 0),
    }
    return render(request, "users/user_profile.html", context)

# ------------------ Dashboard (generic page) ------------------
def dashboard(request):
    username = request.session.get('username')
    if not username:
        messages.error(request, "Please log in first.")
        return redirect('users:login')

    user = users_collection.find_one({"username": username})
    context = {"username": user.get("username", "")} if user else {}
    return render(request, 'users/user_dashboard.html', context)  # <-- use existing template