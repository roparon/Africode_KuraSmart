import io
import os
import uuid
from urllib.parse import quote

import boto3
from botocore.client import Config
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename


def _storage_configured():
    required = (
        os.getenv("AWS_ENDPOINT_URL_S3"),
        os.getenv("AWS_ACCESS_KEY_ID"),
        os.getenv("AWS_SECRET_ACCESS_KEY"),
        os.getenv("STORAGE_BUCKET"),
    )
    return all(required)


def _get_client():
    if not _storage_configured():
        raise RuntimeError(
            "Cloud storage is not configured. "
            "Set AWS_ENDPOINT_URL_S3, AWS_ACCESS_KEY_ID, "
            "AWS_SECRET_ACCESS_KEY and STORAGE_BUCKET."
        )

    return boto3.client(
        "s3",
        endpoint_url=os.getenv("AWS_ENDPOINT_URL_S3"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "auto"),
        config=Config(signature_version="s3v4"),
    )


def upload_image(file, folder, max_size=(600, 600), quality=80):
    """
    Process and upload an image to S3-compatible object storage.

    Returns the object key.
    """

    if not file or not getattr(file, "filename", ""):
        return None

    original_name = secure_filename(file.filename)

    if not original_name:
        raise ValueError("Invalid image filename.")

    file.stream.seek(0)

    image = Image.open(file.stream)
    image = ImageOps.exif_transpose(image)

    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        image = background
    else:
        image = image.convert("RGB")

    image.thumbnail(max_size)

    output = io.BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=quality,
        optimize=True,
    )

    output.seek(0)

    key = f"{folder.strip('/')}/{uuid.uuid4().hex}.jpg"

    client = _get_client()

    client.upload_fileobj(
        output,
        os.getenv("STORAGE_BUCKET"),
        key,
        ExtraArgs={
            "ContentType": "image/jpeg",
            "CacheControl": "public, max-age=31536000, immutable",
        },
    )

    return key


def delete_object(key):
    """Delete a cloud object."""

    if not key or not is_cloud_key(key):
        return False

    client = _get_client()

    client.delete_object(
        Bucket=os.getenv("STORAGE_BUCKET"),
        Key=key,
    )

    return True


def is_cloud_key(value):
    """Identify keys created by KuraSmart cloud storage."""

    if not value:
        return False

    return (
        value.startswith("profiles/")
        or value.startswith("candidates/")
    )


def storage_url(key):
    """Convert a cloud object key into its public URL."""

    if not key:
        return None

    base_url = os.getenv("STORAGE_PUBLIC_BASE_URL", "").rstrip("/")

    if not base_url:
        raise RuntimeError(
            "STORAGE_PUBLIC_BASE_URL is not configured."
        )

    return f"{base_url}/{quote(key, safe='/')}"


def media_url(value):
    """
    Convert cloud keys and legacy local paths into browser URLs.

    Existing local images continue to work.
    """

    if not value:
        return None

    value = str(value).strip()

    if not value:
        return None

    if value.startswith(("http://", "https://")):
        return value

    if is_cloud_key(value):
        return storage_url(value)

    from flask import url_for

    # Legacy candidate records contain only the filename.
    if "/" not in value and "\\" not in value:
        return url_for(
            "static",
            filename=f"uploads/candidates/{value}",
        )

    return url_for(
        "static",
        filename=value.lstrip("/"),
    )
