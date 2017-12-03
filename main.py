#! /usr/bin/env python
"""
Example code to download images via bing search api.

https://azure.microsoft.com/en-us/services/cognitive-services/bing-image-search-api/
"""
import os
import time
import logging
from bingimages import BingImageSearch, download_imgs

# Logger setting
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
hdr = logging.StreamHandler()
hdr.setLevel(logging.DEBUG)
fmt = logging.Formatter(fmt='%(asctime)s [%(levelname)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
hdr.setFormatter(fmt)
logger.addHandler(hdr)

# Directory to save materials into
URL_DIR = 'url'
ROOT_IMGDIR = 'imgs'

# API Key
# https://azure.microsoft.com/en-us/try/cognitive-services/
SUBSCRIPTION_KEY = "your_API_key_here"


def fetch_url(kwds_dict, max_count=None):
    """Make url list of images to download.

    Paramaters:
        kwd_dict: dict {'group1': ('search keywords1, search keyword2', ...),
                         'group2': 'search keyword'}
        max_count: int Number of images(URLs) to fetch
    """

    SLEEP_SEC = 5

    # Make directory to save url list into.
    save_path = os.path.join(URL_DIR, 'url_{group}.txt')
    os.makedirs(URL_DIR, exist_ok=True)

    bis = BingImageSearch(SUBSCRIPTION_KEY, logger)

    url_paths = {}
    for grp, kwds in kwds_dict.items():

        if isinstance(kwds, str):
            iter_kwd = (kwds,)
        else:
            iter_kwd = kwds

        # Fetch URL
        for kwd in iter_kwd:
            bis.search(kwd, max_count=max_count)
            time.sleep(SLEEP_SEC)

        # Save URL list
        bis.save(save_path.format(group=grp))
        url_paths[grp] = save_path.format(group=grp)

    return url_paths


def main():

    # Search keywords
    # {'keyword group': ('search keyword1', 'search keyword2')}
    kwds_dict = {
                 'ts_white': ('white t-shirt fashion',
                              'white t-shirt dressing well'),
                 'ts_blue': ('blue t-shirt fashion',
                               'blue t-shirt dressing well'),
                 }

    # Make URL list
    paths_urllist = fetch_url(kwds_dict)

    # Download images
    for grp, path_urllist in paths_urllist.items():

        with open(path_urllist, 'r') as f:
            urllist = [line[:-1] for line in f]

        # Download images
        dest_dir = '{}/{}'.format(ROOT_IMGDIR, grp)
        download_imgs(urllist, dest_dir=dest_dir,
                      prefix='img_{}'.format(grp), logger=logger)


if __name__ == '__main__':
    main()
