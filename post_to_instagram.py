import os
import sys
import time
import requests

GRAPH_URL = "https://graph.instagram.com"


def post_image(image_url, caption):
    token = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    user_id = os.environ["INSTAGRAM_USER_ID"]

    # 1. Create media container
    create_url = f"{GRAPH_URL}/{user_id}/media"

    response = requests.post(
        create_url,
        params={
            "image_url": image_url,
            "caption": caption,
            "access_token": token,
        },
        timeout=60,
    )

    response.raise_for_status()

    container = response.json()
    creation_id = container.get("id")

    if not creation_id:
        raise RuntimeError(f"Container creation failed: {container}")

    print(f"Media container created: {creation_id}")

    # 2. Wait until Instagram finishes processing the image
    status_url = f"{GRAPH_URL}/{creation_id}"

    for attempt in range(10):
        response = requests.get(
            status_url,
            params={
                "fields": "status_code,status",
                "access_token": token,
            },
            timeout=60,
        )

        response.raise_for_status()
        status = response.json()

        status_code = status.get("status_code")
        status_message = status.get("status")

        print(
            f"Container status ({attempt + 1}/10): "
            f"{status_code} - {status_message}"
        )

        if status_code == "FINISHED":
            break

        if status_code == "ERROR":
            raise RuntimeError(
                f"Instagram container processing failed: {status}"
            )

        if status_code == "EXPIRED":
            raise RuntimeError(
                f"Instagram container expired: {status}"
            )

        time.sleep(30)

    else:
        raise RuntimeError(
            "Instagram container did not become FINISHED within 5 minutes."
        )

    # 3. Publish the finished container
    publish_url = f"{GRAPH_URL}/{user_id}/media_publish"

    response = requests.post(
        publish_url,
        params={
            "creation_id": creation_id,
            "access_token": token,
        },
        timeout=60,
    )

    if not response.ok:
        print("Instagram publish error:")
        print(response.text)

    response.raise_for_status()

    result = response.json()

    print(f"Instagram post published successfully: {result}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python post_to_instagram.py IMAGE_URL")
        sys.exit(1)

    image_url = sys.argv[1]

    caption = os.getenv(
        "INSTAGRAM_CAPTION",
        "Your caption here"
    )

    post_image(image_url, caption)
