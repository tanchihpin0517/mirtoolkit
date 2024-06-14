import requests


def download(url, file):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes

        # Write the content to the temporary file
        file.write(response.content)
        file.seek(0)  # Rewind the file to the beginning
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
