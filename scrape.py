import requests
from fake_useragent import UserAgent
import downloader
from utils import make_directory, directory_exists, contains_illegal_characters

# change this obviously
subreddit = "sfmcompileclub"

# set to 0 if points/upvote count is not important
minimum_points = 0

# hour, day, week, month, year, all
r_timeframe = "all"
# controversial, best, hot, new, random, rising, top
r_listing = "top"

# for pagination, or to access more than 100 posts in sequential order,
# the request url must contain the "after" attribute.
# after=null (implicit) => start off at the top, else after some post id
# therefore it is required to save the last post id of a page
# in order to access the next page.
# the post id is actually the 'name' field.
last_post = "null"

ua = UserAgent()

total_posts = 0
total_accepted = 0
total_rejected = 0


def expose_subreddit():
    return subreddit


def post_qualifies(post):
    # updoots
    points = int(post['ups'])
    return points >= minimum_points


# max 100 posts per request
def make_request_url():
    base_url = "https://reddit.com/r/"
    request_string = f"{base_url}{subreddit}/{r_listing}.json?limit=100&t={r_timeframe}&after={last_post}"
    return request_string


def fetch_json(url):
    headers = {"User-Agent": ua.random}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        # throw an exception maybe?
        print(f"Error: {url} received http response code {response.status_code}")
    return response.json()


def grab_media_urls(posts):
    global total_rejected

    urls = []
    for p in posts:
        if not post_qualifies(p['data']):
            total_rejected += 1
            print(f"[[Post id={p['data']['id']}]] title=[{p['data']['title']}] rejected.")
            continue
        urls.append(p['data']['url'])
    return urls


def scrape_subreddit_page(page):

    global last_post

    print(f"Scraping page {page}: last_post={last_post}.")
    url = make_request_url()
    posts = fetch_json(url)

    length = len(posts['data']['children'])
    last_post = posts['data']['children'][length-1]['data']['name']

    media = grab_media_urls(posts['data']['children'])
    print(f"media length={len(media)}")
    print(media)
    for m in media:
        downloader.download(m)

    return length


def main():
    global total_posts, total_rejected, total_accepted

    page_number = 1
    batch_size = 100

    # batch_size will be less than 100 when there are no more posts
    # beyond the page currently being worked on
    while batch_size == 100:
        batch_size = scrape_subreddit_page(page_number)
        total_posts += batch_size
        page_number += 1

    print(f"Total: {total_posts} of which {total_accepted} downloaded, and {total_rejected} were rejected.")


if __name__ == '__main__':
    if contains_illegal_characters(subreddit):
        print("Bad subreddit string!")
        exit(1)
#    if directory_exists(subreddit):
#        print("This directory already exists!")
#        exit(1)
    make_directory(subreddit)
    main()
