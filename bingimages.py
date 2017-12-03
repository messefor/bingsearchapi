"""
Utils for download images via Bing image search api.

Reference:
Image Search API - v7
https://dev.cognitive.microsoft.com/docs/services/8336afba49a84475ba401758c0dbf749/operations/56b4433fcf5ff8098cef380c

Bing Image Search Documentation
https://docs.microsoft.com/pdfstore/en-us/Azure.azure-documents/live/cognitive-services/Bing-Image-Search.pdf

https://stackoverflow.com/questions/44560203/using-bing-image-api-in-jave-to-search-for-images
"""
import os
import time
import pickle

import urllib.parse
import requests

# Request timeout setting
TIMEOUT = 10

# Extentions to download
TARGET_EXT = ('.jpg', '.JPG', '.jpeg', '.png')


class BingImageSearch:

    proto = 'https://'
    host = "api.cognitive.microsoft.com"
    path = "/bing/v7.0/images/search"

    def __init__(self, subscriptionKey, logger):

        self.url = BingImageSearch.proto + BingImageSearch.host + \
                   BingImageSearch.path

        self.key = subscriptionKey
        self.headers = {'Ocp-Apim-Subscription-Key': subscriptionKey}

        self.logger = logger

        self.nextoffset = 0
        self.imgs_per_page = 150
        # We can request at most 150 * 10 = 1500 images per kwd
        self.max_req = 10

        self.est_max = 1000

        self.url_fetched = []
        self.n_fetched = 0
        self.n_fetched_total = 0

    def _get_params(self, kwd):
        query_dict = {'q': kwd,
                      'count': self.imgs_per_page,
                      'offset': self.nextoffset}
        return urllib.parse.urlencode(query_dict)

    def _search(self, kwd):
        r = requests.get(self.url, headers=self.headers,
                         params=self._get_params(kwd), timeout=TIMEOUT)
        if r.status_code == 200:
            return r
        else:
            raise Exception(r.text)

    def update_values(self, response):
        result_dict = response.json()
        result_values = result_dict['value']
        urls = [v['contentUrl'] for v in result_values]
        self.url_fetched.extend(urls.copy())
        self.nextoffset = result_dict['nextOffset']
        self.est_max = result_dict['totalEstimatedMatches']
        self.n_fetched = len(result_values)
        self.n_fetched_total += len(result_values)

    def print_status(self):
        self.logger.info('total urls: %s', self.n_fetched_total)
        self.logger.info('estimated max: %s', self.est_max)
        self.logger.info('nextoffset: %s', self.nextoffset)

    def _info_at_start(self, req_count, kwd, max_count):
        self.logger.info('=' * 40)
        self.logger.info('Start request %s...', req_count)
        self.logger.info('Search keyword: %s', kwd)
        self.logger.info('max count: %s', max_count)
        self.logger.info('=' * 40)

    def search(self, kwd, max_count=None, sleep_time=2):
        max_count = self.est_max if max_count is None else max_count
        req_count = 0
        while self.est_max >= self.n_fetched_total and\
              max_count >= self.n_fetched_total:

            self._info_at_start(req_count, kwd, max_count)

            r = self._search(kwd)
            self.update_values(r)
            self.print_status()

            # Break when reqest number exceed max reqest
            # or number of fetched images are too small
            if req_count > self.max_req or\
               self.n_fetched < self.imgs_per_page / 2:
                self.logger.warning('Break for request count per keyword\
                exceeded expected or number of images fetched are small.\
                max_count: %s, req_count: %s', max_count, req_count)
                break

            req_count += 1
            time.sleep(sleep_time)

        self.nextoffset = 0
        self.n_fetched_total = 0

        self.logger.info('Done.')

    @staticmethod
    def _write_list(line_list, f):
        for line in line_list:
            f.write(line + '\n')

    def save(self, save_path):
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        if os.path.splitext(save_path) in ('.pkl', '.pickle'):
            open_mode = 'wb'
            save_func = pickle.dump
        else:
            open_mode = 'w'
            save_func = self._write_list

        with open(save_path, open_mode) as f:
            save_func(list(set(self.url_fetched)), f)


def download_imgs(img_urllist, dest_dir, prefix, logger, sleep_time=0.5):
    """Download images located in urls."""
    os.makedirs(dest_dir, exist_ok=True)
    for idx, url in enumerate(img_urllist):
        logger.info('file %s. downloading %s', idx, url)
        try:
            r = requests.get(url, stream=True)
        except (requests.exceptions.SSLError,
                requests.exceptions.ConnectionError):
            logger.error('file %s ConnectionError: %s', idx, url)
        else:
            if r.status_code == 200:
                _, ext = os.path.splitext(url)
                ext = ext.split('?')[0]
                if ext in TARGET_EXT:
                    file_path = '{}/{}_{:04}{}'.format(dest_dir, prefix,
                                                       idx, ext)
                    with open(file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024):
                            f.write(chunk)
            else:
                logger.warning('Failed status code: %s', r.status_code)
        time.sleep(sleep_time)
