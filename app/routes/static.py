from flask import Blueprint, render_template

static_pages = Blueprint("static_pages", __name__)

@static_pages.route("/how-it-works")
def how_it_works():
    return render_template("partials/how_it_works_modal.html")

@static_pages.route("/privacy-policy")
def privacy_policy():
    return render_template("partials/privacy_modal.html")

@static_pages.route("/terms-and-conditions")
def terms_and_conditions():
    return render_template("static_pages/terms_and_conditions.html")

@static_pages.route("/help-center")
def help_center():
    return render_template("help_center.html")
