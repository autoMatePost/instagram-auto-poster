import os
import sys
import time
import requests

GRAPH_URL = "https://graph.instagram.com"


def wait_for_container(creation_id, token):
    status_url = f"{GRAPH_URL}/{creation_id}"

    for attempt in range(20):
        response = requests.get(
            status_url,
            params={
                "fields": "status_code,status",
                "access_token": token,
            },
            timeout=60,
        )

        response.raise_for_status()
        data = response.json()

        status_code = data.get("status_code")
        print(f"Container status ({attempt + 1}/20): {data}")

        if status_code == "FINISHED":
            return

        if status_code in ("ERROR", "EXPIRED"):
            raise RuntimeError(
                f"Instagram container failed: {data}"
            )

        time.sleep(30)

    raise RuntimeError(
        "Container did not finish within the allowed time."
    )


def publish_container(user_id, creation_id, token):
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

    print(f"Published successfully: {response.json()}")


def post_image(user_id, image_url, caption, token):
    response = requests.post(
        f"{GRAPH_URL}/{user_id}/media",
        params={
            "image_url": image_url,
            "caption": caption,
            "access_token": token,
        },
        timeout=60,
    )

    response.raise_for_status()

    creation_id = response.json().get("id")

    if not creation_id:
        raise RuntimeError(
            f"Image container creation failed: {response.text}"
        )

    print(f"Image container created: {creation_id}")

    wait_for_container(creation_id, token)
    publish_container(user_id, creation_id, token)


def post_reel(user_id, video_url, caption, token):
    response = requests.post(
        f"{GRAPH_URL}/{user_id}/media",
        params={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": token,
        },
        timeout=60,
    )

    response.raise_for_status()

    creation_id = response.json().get("id")

    if not creation_id:
        raise RuntimeError(
            f"Reel container creation failed: {response.text}"
        )

    print(f"Reel container created: {creation_id}")

    wait_for_container(creation_id, token)
    publish_container(user_id, creation_id, token)


def main():
    if len(sys.argv) < 2:
        print("Usage: python post_to_instagram.py FILE_URL")
        sys.exit(1)

    file_url = sys.argv[1]

    token = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    user_id = os.environ["INSTAGRAM_USER_ID"]

    caption = os.getenv(
        "INSTAGRAM_CAPTION",
        "Your caption here"
    )

    if file_url.lower().endswith((".mp4", ".mov")):
        print("Detected: VIDEO / REEL")
        post_reel(user_id, file_url, caption, token)

    elif file_url.lower().endswith(
        (".jpg", ".jpeg", ".png")
    ):
        print("Detected: IMAGE")
        post_image(user_id, file_url, caption, token)

    else:
        raise RuntimeError(
            f"Unsupported file type: {file_url}"
        )


if __name__ == "__main__":
    main()
