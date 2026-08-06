"""
Publishes a single image + caption to Instagram via the Instagram Platform
API (Instagram API with Instagram Login — the standalone, non-Facebook-Page
flow Meta recommends for single-account apps as of 2026).

Requires two repo secrets (set these up per SETUP_META.md):
  IG_USER_ID           - your Instagram professional account's numeric ID
                          (the Instagram-scoped user ID from the Instagram
                          Login flow, not a Facebook Page-linked ID)
  IG_ACCESS_TOKEN       - a long-lived Instagram User access token with
                           instagram_business_basic +
                           instagram_business_content_publish

The image must already be reachable at a public HTTPS URL (the
orchestrator uploads it to GitHub first — see github_host.py).
"""
import os
import time

import requests

GRAPH_API_VERSION = "v26.0"
GRAPH_BASE = f"https://graph.instagram.com/{GRAPH_API_VERSION}"


def _creds():
    user_id = os.environ["IG_USER_ID"]
    token = os.environ["IG_ACCESS_TOKEN"]
    return user_id, token


def create_media_container(image_url, caption):
    user_id, token = _creds()
    resp = requests.post(
        f"{GRAPH_BASE}/{user_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": token},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def wait_until_ready(container_id, timeout_s=120, poll_every=3):
    _, token = _creds()
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        resp = requests.get(
            f"{GRAPH_BASE}/{container_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        )
        resp.raise_for_status()
        status = resp.json().get("status_code")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            raise RuntimeError(f"Media container {container_id} failed to process")
        time.sleep(poll_every)
    raise TimeoutError(f"Media container {container_id} not ready after {timeout_s}s")


def publish_container(container_id):
    user_id, token = _creds()
    resp = requests.post(
        f"{GRAPH_BASE}/{user_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def post_image(image_url, caption):
    """Full publish flow. Returns the published media ID."""
    container_id = create_media_container(image_url, caption)
    wait_until_ready(container_id)
    media_id = publish_container(container_id)
    return media_id
