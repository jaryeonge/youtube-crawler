import argparse
import json
import multiprocessing as mp
import os
import time

from crawling_module import *
from utils.crawling_logger import default_logger
from utils.parse_keywords import extract_keywords

API_KEY_PATH = './config/api_key.json'
logger = default_logger()


class CrawlingProgram:
    def __init__(self, config):
        self.config = config
        self.cnt = 0
        self._load_api_key_list()
        self._load_keyword_list()

        os.makedirs(self.config.save_path, exist_ok=True)

    def _load_api_key_list(self):
        json_object = json.load(open(API_KEY_PATH, 'r'))
        self.api_key_list = json_object['key_list']

    def _load_keyword_list(self):
        self.keyword_list = extract_keywords(self.config.keywords)

    def id_crawling(self, q: mp.Queue):
        try:
            if self.config.dynamic_mode:
                id_module = DynamicCrawler(num=self.config.num, search_option=self.config.search_option,
                                           keyword_list=self.keyword_list, window=self.config.window)
            else:
                id_module = StaticCrawler(search_option=self.config.search_option,
                                          keyword_list=self.keyword_list)

            gen = id_module.make_gen()
            for result_list in gen:
                for data in result_list:
                    q.put([data['video_id'], data['keyword']])

            q.put('end')
        except Exception as e:
            logger.error(e)
            q.put('end')

    def meta_crawling(self, q: mp.Queue):
        meta_module = MetaCrawler(self.api_key_list)
        while True:
            while q.empty():
                time.sleep(0.01)
            queue_data = q.get()
            if queue_data == 'end':
                break
            else:
                vod_id, keyword = queue_data
            data = meta_module.crawling_meta(str(vod_id), str(keyword))
            if data is None:
                continue
            elif data == 'end':
                break
            else:
                self.save_result(data)

    def save_result(self, data):
        path = os.path.join(self.config.save_path, 'meta.json')
        json.dump({self.cnt: data}, open(path, 'a', encoding='utf8'), ensure_ascii=False)
        self.cnt += 1

    def run(self):
        queue = mp.Queue()
        id_process = mp.Process(target=self.id_crawling, args=(queue,))
        meta_process = mp.Process(target=self.meta_crawling, args=(queue,))

        logger.info('Process started')
        id_process.start()
        meta_process.start()

        meta_process.join()
        logger.info('Process is complete')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Program to crawl YouTube meta data')
    parser.add_argument('-k', '--keywords', type=str, help='path of keywords list')
    parser.add_argument('-n', '--num', default=20, type=int, help='number of vod per keyword')
    parser.add_argument('-s', '--search_option', default=0, help='search option')
    parser.add_argument('-sp', '--save_path', default='./result', help='path of saving result')
    parser.add_argument('-d', '--dynamic_mode', default=False, type=bool, help='Whether to do dynamic crawling or not')
    parser.add_argument('-w', '--window', default=True, type=bool, help='Whether the OS is Window or not')
    args = parser.parse_args()

    main = CrawlingProgram(config=args)
    main.run()
