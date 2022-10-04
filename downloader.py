import requests
from fake_useragent import UserAgent
import re
import scrape
import utils

ua = UserAgent()
filename_pattern = r"\/([^\/]+\.[a-zA-Z0-9]+)$"
clean_url_pattern = r"(https?[^\?]+)"


def clean_url(url):
    results = re.findall(clean_url_pattern, url)
    return results[0]


def url_to_filename(url):
    url = clean_url(url)
    results = re.findall(filename_pattern, url)
    return results[0]


def save(url):
    filename = url_to_filename(url)
    name = f"{scrape.expose_subreddit()}/{filename}"
    headers = {"User-Agent": ua.random}
    response = requests.get(url, headers=headers)

    if utils.file_exists(name):
        print(f"File {filename} (from {url}) already exists. Skipping.")
        return

    with open(name, "wb") as f:
        f.write(response.content)


def save_as(url, name):
    headers = {"User-Agent": ua.random}
    path = f"{scrape.expose_subreddit()}/{name}"
    response = requests.get(url, headers=headers)

    if utils.file_exists(path):
        print(f"File {name} ({path}) (from {url}) already exists. Skipping.")
        return

    with open(path, "wb") as f:
        f.write(response.content)


def download_redgifs(url):
    pass

# assumes that basename only has 3 dots
# https://i   .   redd   .   it/blababla    .    jpg
def add_gallery_index(basename, index):
    parts = basename.split('.')
    parts[2] += "_" + str(index)
    return '.'.join(parts)


def download_reddit_gallery(url):
    new_url = url.replace("/gallery/", "/comments/")
    new_url += ".json"
    headers = {"User-Agent": ua.random}
    response = requests.get(new_url, headers=headers)
    json_resp = response.json()
    print(url)
    print(json_resp)
    if json_resp[0]['data']['children'][0]['data']['selftext'] == "[removed]" or json_resp[1]['media'] is None:
        print("gallery removed, skipping.")
        return
    j = json_resp[0]['data']['children'][0]['data']['media_metadata']
    gallery_index = 1
    basename = ""
    for c in j:
        image_url = j[c]['o'][0]['u']
        image_url = image_url.replace("preview.", "i.")
        image_url_clean = clean_url(image_url)
        if gallery_index == 1:
            basename = image_url_clean
        image_url_clean = add_gallery_index(basename, gallery_index)
        print(f"gallery_idx={gallery_index}; iuc={image_url_clean}")
        save_as(image_url, url_to_filename(image_url_clean))
        gallery_index += 1
    print(f"[reddit gallery] saved {url}")


def download_regular_file(url):
    print(f"saved url {url}")
    save(url)


def download(url):
    file_ext = [".png", ".jpg", ".jpeg", ".webm", ".mp4"]

    if "redgifs.com" in url:
        download_redgifs(url)
    elif "reddit.com/gallery/" in url:
        download_reddit_gallery(url)
    else:
        for ext in file_ext:
            if ext in url:
                download_regular_file(url)
                return

        print(f"Link not supported: {url}")

