import os
import json
import time
import requests
from pathlib import Path

GRAPH_URL = "https://graph.instagram.com"

STATE_FILE = Path("state.json")


def load_state():
    if not STATE_FILE.exists():
        return {"next_index": 0}

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_reels():
    folder = Path("images")

    # केवल 001.mp4, 002.mp4 ... जैसी numbered Reels लें
    files = [
        file
        for file in folder.iterdir()
        if file.is_file()
        and file.suffix.lower() == ".mp4"
        and file.stem.isdigit()
    ]

    return sorted(files, key=lambda file: int(file.stem))


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

        print(
            f"Container status ({attempt + 1}/20): {data}"
        )

        status_code = data.get("status_code")

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


def publish_reel(user_id, file_url, caption, token):
    # Create Reel container
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

    if not response.ok:
        print("Instagram container creation error:")
        print(response.text)

    response.raise_for_status()

    creation_id = response.json().get("id")

    if not creation_id:
        raise RuntimeError(
            f"Reel container creation failed: {response.text}"
        )

    print(f"Reel container created: {creation_id}")

    # Wait until Instagram finishes processing
    wait_for_container(creation_id, token)

    # Publish Reel
    response = requests.post(
        f"{GRAPH_URL}/{user_id}/media_publish",
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

    print(
        f"Published successfully: {response.json()}"
    )


def main():
    token = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    user_id = os.environ["INSTAGRAM_USER_ID"]

    caption = os.getenv(
        "INSTAGRAM_CAPTION",
        "Your caption here"
    )

    reels = get_reels()

    if not reels:
        raise RuntimeError(
            "No numbered MP4 Reels found in images folder."
        )

    state = load_state()

    next_index = state.get("next_index", 0)

    if next_index >= len(reels):
        print("All Reels have been posted.")
        return

    selected_file = reels[next_index]

    print(
        f"Selected Reel "
        f"{next_index + 1}/{len(reels)}: "
        f"{selected_file.name}"
    )

    repository = os.environ["GITHUB_REPOSITORY"]
    branch = os.getenv("GITHUB_REF_NAME", "main")

    file_url = (
        f"https://raw.githubusercontent.com/"
        f"{repository}/{branch}/images/"
        f"{selected_file.name}"
    )

    print(f"Public URL: {file_url}")

    print("Detected: REEL")

    publish_reel(
        user_id,
        file_url,
        caption,
        token
    )

    # केवल successful publish के बाद queue आगे बढ़े
    state["next_index"] = next_index + 1

    save_state(state)

    print(
        f"Queue advanced: "
        f"next_index={state['next_index']}"
    )


if __name__ == "__main__":
    main()
