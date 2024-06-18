import requests


def download(url, file):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes

        with open(file, "wb") as f:
            f.write(response.content)
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
