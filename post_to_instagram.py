
import os
import sys
import requests

GRAPH_URL = "https://graph.instagram.com"


def post_image(image_url, caption):
    token = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    user_id = os.environ["INSTAGRAM_USER_ID"]

    # Step 1: Create media container
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
        raise RuntimeError(f"Media container was not created: {container}")

    print(f"Media container created: {creation_id}")

    # Step 2: Publish media
    publish_url = f"{GRAPH_URL}/{user_id}/media_publish"

    response = requests.post(
        publish_url,
        params={
            "creation_id": creation_id,
            "access_token": token,
        },
        timeout=60,
    )

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
