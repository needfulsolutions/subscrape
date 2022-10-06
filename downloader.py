import requests
from fake_useragent import UserAgent
import re
import scrape
import utils

ua = UserAgent()
filename_pattern = r"\/([^\/]+\.[a-zA-Z0-9]+)$"
clean_url_pattern = r"(https?[^\?]+)"
redgifs_pattern = r"watch\/([a-zA-Z0-9]+)"
redgifs_url_to_filename_pattern = r"\/([a-zA-Z0-9\.]+)$"


def redgifs_url_to_filename(url):
    results = re.findall(redgifs_url_to_filename_pattern, url)
    return results[0]


def find_redgifs_id(url):
    results = re.findall(redgifs_pattern, url)
    return results[0]


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

    scrape.total_accepted += 1


def save_as(url, name):
    headers = {"User-Agent": ua.random}
    path = f"{scrape.expose_subreddit()}/{name}"
    response = requests.get(url, headers=headers)

    if utils.file_exists(path):
        print(f"File {name} ({path}) (from {url}) already exists. Skipping.")
        return

    with open(path, "wb") as f:
        f.write(response.content)

    scrape.total_accepted += 1


def redgifs_save_as(url, name, session):
    path = f"{scrape.expose_subreddit()}/{name}"

    with session.get(url, stream=True) as r:
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def download_redgifs(url):
    rid = find_redgifs_id(url)
    request_url = f"https://api.redgifs.com/v2/gifs/{rid}"
    rg_session = requests.Session()
    response = rg_session.get(request_url)
    saved_as_hd = False
    if response.status_code != 200:
        print(f"gif not found: {url}")
        return

    data = response.json()
    if not json_keypair_exists('hd', data['gif']['urls']):
        if not json_keypair_exists('sd', data['gif']['urls']):
            print(f"no gif found in json response: {url}")
            print(data)
            return
        cleaned_url = clean_url(data['gif']['urls']['sd'])
        clean_filename = redgifs_url_to_filename(cleaned_url)
        redgifs_save_as(data['gif']['urls']['sd'], clean_filename, rg_session)
    else:
        cleaned_url = clean_url(data['gif']['urls']['hd'])
        clean_filename = redgifs_url_to_filename(cleaned_url)
        redgifs_save_as(data['gif']['urls']['hd'], clean_filename, rg_session)
        saved_as_hd = True

    print(f"redgif saved ({'hd' if saved_as_hd else 'sd'}): {url}")


# assumes that basename only has 3 dots
# https://i   .   redd   .   it/blababla    .    jpg
def add_gallery_index(basename, index):
    parts = basename.split('.')
    parts[2] += "_" + str(index)
    return '.'.join(parts)

def json_keypair_exists(key, json):
    if not key in json:
        return False
    if json[key] is None:
        return False
    return True

def download_reddit_gallery(url):
    new_url = url.replace("/gallery/", "/comments/")
    new_url += ".json"
    headers = {"User-Agent": ua.random}
    response = requests.get(new_url, headers=headers)
    data = response.json()
    print(url)
    post_is_removed = data[0]['data']['children'][0]['data']['selftext'] == "[removed]"
    media_exists = 'media_metadata' in data[0]['data']['children'][0]['data']

    if post_is_removed or not media_exists:
        print("gallery removed, skipping.")
        scrape.total_rejected += 1
        return

    media = data[0]['data']['children'][0]['data']['media_metadata']
    if media is None:
        print("gallery removed, skipping.")
        scrape.total_rejected += 1
        return

    gallery_index = 1
    basename = ""
    for c in media:
        if not json_keypair_exists('o', media[c]):
            print("no image under o tag found")
            return
        image_url = media[c]['o'][0]['u']
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
    file_ext = [".png", ".jpg", ".jpeg", ".webm", ".mp4", ".gif"]

    if "imgflip" in url:
        print(f"imgflip is broken, skipping {url}")
        return

    if "redgifs.com" in url:
        download_redgifs(url)

        return
    elif "reddit.com/gallery/" in url:
        download_reddit_gallery(url)
        return
    else:
        for ext in file_ext:
            if ext in url:
                download_regular_file(url)
                return

        print(f"Link not supported: {url}")

