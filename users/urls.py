from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    # Home / Info
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("faq/", views.faq, name="faq"),

    # Login / Signup / Admin
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_user, name="logout_user"),        # <-- logout
    path("admin-login/", views.admin_login, name="admin_login"),
    path("signup/", views.signup, name="signup"),

    # OTP Verification pages
    path("verify-signup-otp/", views.verify_signup_otp, name="verify_signup_otp"),
    path("verify-reset-otp/", views.verify_reset_otp, name="verify_reset_otp"),
    path("verify-account/", views.verify_account, name="verify_account"),

    # Forgot Password / Set New Password
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("set-new-password/", views.set_new_password, name="set_new_password"),

    # User dashboard + profile
    # User dashboard + profile
    path("dashboard/", views.dashboard, name="dashboard"),  # This is the generic dashboard
    path("user-dashboard/", views.user_dashboard, name="user_dashboard"),
    path("profile/", views.user_profile, name="user_profile"),

    path("admin-login/", views.admin_login, name="admin_login"),
    path("admin-logout/", views.admin_logout, name="admin_logout"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-lost-items/", views.admin_lost_items, name="admin_lost_items"),
    path("admin-found-items/", views.admin_found_items, name="admin_found_items"),
    path("admin-matched-items/", views.admin_matched_items, name="admin_matched_items"),
    path("admin-recovered-items/", views.admin_recovered_items, name="admin_recovered_items"),

]
