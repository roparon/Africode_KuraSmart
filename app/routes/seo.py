from flask import Blueprint, Response, current_app
from html import escape

seo_bp = Blueprint("seo", __name__)


def _site_url():
    return (
        current_app.config.get("SITE_URL")
        or "https://kurasmart.vercel.app"
    ).rstrip("/")


@seo_bp.route("/robots.txt")
def robots_txt():
    base = _site_url()

    body = "\n".join([
        "User-agent: *",
        "Allow: /",
        "",
        "Disallow: /admin/",
        "Disallow: /auth/",
        "Disallow: /dashboard",
        "Disallow: /vote/",
        "Disallow: /api/",
        "Disallow: /login",
        "Disallow: /logout",
        "Disallow: /register",
        "Disallow: /forgot_password",
        "Disallow: /reset_password/",
        "Disallow: /notifications",
        "Disallow: /scheduler",
        "",
        f"Sitemap: {base}/sitemap.xml",
        "",
    ])

    return Response(body, mimetype="text/plain")


@seo_bp.route("/sitemap.xml")
def sitemap_xml():
    base = _site_url()

    # Only include confirmed public pages that currently return
    # successful responses without authentication.
    public_pages = [
        ("/", "daily", "1.0"),
        ("/help", "monthly", "0.5"),
        ("/how-it-works", "monthly", "0.7"),
        ("/privacy-policy", "yearly", "0.3"),
        ("/terms-and-conditions", "yearly", "0.3"),
    ]

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for path, changefreq, priority in public_pages:
        lines.append("  <url>")
        lines.append(
            f"    <loc>{escape(base + path)}</loc>"
        )
        lines.append(
            f"    <changefreq>{changefreq}</changefreq>"
        )
        lines.append(
            f"    <priority>{priority}</priority>"
        )
        lines.append("  </url>")

    lines.append("</urlset>")

    return Response(
        "\n".join(lines),
        mimetype="application/xml",
    )
