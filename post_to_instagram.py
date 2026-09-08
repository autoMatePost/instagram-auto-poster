import os
import sys
import time
import requests
from pathlib import Path

GRAPH_URL = "https://graph.instagram.com"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTENSIONS = {".mp4", ".mov"}


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
    response = requests.post(
        f"{GRAPH_URL}/{user_id}/media_publish",
        params={
            "creation_id": creation_id,
            "access_token": token,
        },
        timeout=60,
    )

    if not response.ok:
        print(response.text)

    response.raise_for_status()
    print(f"Published successfully: {response.json()}")


def post_image(user_id, file_url, caption, token):
    response = requests.post(
        f"{GRAPH_URL}/{user_id}/media",
        params={
            "image_url": file_url,
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


def post_reel(user_id, file_url, caption, token):
    response = requests.post(
        f"{GRAPH_URL}/{user_id}/media",
        params={
            "media_type": "REELS",
            "video_url": file_url,
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


def get_files():
    folder = Path("images")

    files = [
        file for file in folder.iterdir()
        if file.is_file()
        and file.suffix.lower()
        in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
    ]

    return sorted(files, key=lambda file: file.name.lower())


def main():
    token = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    user_id = os.environ["INSTAGRAM_USER_ID"]

    caption = os.getenv(
        "INSTAGRAM_CAPTION",
        "Your caption here"
    )

    files = get_files()

    if not files:
        raise RuntimeError("No images or videos found in images folder.")

    print("Files found:")
    for file in files:
        print(f" - {file}")

    # For now, select the first file.
    # Queue/state system will be added next.
    selected_file = files[0]

    print(f"Selected file: {selected_file}")

    filename = selected_file.name

    # GitHub raw public URL
    repository = os.environ["GITHUB_REPOSITORY"]
    branch = os.getenv("GITHUB_REF_NAME", "main")

    file_url = (
        f"https://raw.githubusercontent.com/"
        f"{repository}/{branch}/images/{filename}"
    )

    print(f"Public URL: {file_url}")

    extension = selected_file.suffix.lower()

    if extension in VIDEO_EXTENSIONS:
        print("Detected: VIDEO / REEL")
        post_reel(user_id, file_url, caption, token)

    elif extension in IMAGE_EXTENSIONS:
        print("Detected: IMAGE")
        post_image(user_id, file_url, caption, token)

    else:
        raise RuntimeError(
            f"Unsupported file type: {extension}"
        )


if __name__ == "__main__":
    main()
