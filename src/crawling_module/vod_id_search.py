import os
import requests
import re
import json
import time
import random

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

from utils.crawling_logger import default_logger

SEARCH_OPTION = {
    0: 'EgIQAQ%3D%3D',  # 동영상+모두+관련성
    1: 'CAISAhAB',  # 동영상+모두+업로드날짜
    2: 'CAMSAhAB',  # 동영상+모두+조회수
    3: 'CAESAhAB',  # 동영상+모두+평점
    4: 'EgQIBBAB',  # 동영상+이번달+관련성
    5: 'CAISBAgEEAE%3D',  # 동영상+이번달+업로드날짜
    6: 'CAMSBAgEEAE%3D',  # 동영상+이번달+조회수
    7: 'CAESBAgEEAE%3D',  # 동영상+이번달+평점
    8: 'EgQIBRAB',  # 동영상+올해+관련성
    9: 'CAISBAgFEAE%3D',  # 동영상+올해+업로드날짜
    10: 'CAMSBAgFEAE%3D',  # 동영상+올해+조회수
    11: 'CAESBAgFEAE%3D'  # 동영상+올해+평점
}

logger = default_logger()


class StaticCrawler:
    def __init__(self, search_option, keyword_list):
        self.search_option = SEARCH_OPTION[int(search_option)]
        self.keyword_list = keyword_list

        self.search_url = 'https://www.youtube.com/results?'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
        self.retry_delay = 1.5
        self.delay_range = (1, 3)

    def crawling(self, keyword):
        params = {'search_query': keyword,
                  'sp': self.search_option}
        result_list = []

        # request
        try:
            response = requests.get(url=self.search_url, params=params, headers=self.headers)
        except Exception as e:
            logger.error(e)
            logger.info('retry...')
            time.sleep(self.retry_delay)
            try:
                response = requests.get(url=self.search_url, params=params, headers=self.headers)
            except Exception as e:
                logger.error(e)
                return None

        # parsing
        try:
            res_text = response.text
            compiler = re.compile(r'ytInitialData\s*=\s*(\{.*?\});')

            res_yt = compiler.findall(res_text)
            res_json = json.loads(res_yt[0])
            res_section = res_json['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
        except KeyError as e:
            logger.error(e)
            return None

        # filtering ad
        items = None
        for sec in res_section:
            try:
                test = sec['itemSectionRenderer']['contents'][-1]['videoRenderer']
                items = sec['itemSectionRenderer']['contents']
            except KeyError:
                continue

        if items is None:
            return None

        for item in items:
            try:
                info = item['videoRenderer']

                video_id = info['videoId']
                video_url = f'https://www.youtube.com/watch?v={video_id}'
                title = info['title']['runs'][0]['text']

                result_dict = {'video_id': video_id,
                               'video_url': video_url,
                               'title': title,
                               'keyword': keyword}
                result_list.append(result_dict)

            except KeyError:
                continue

        return result_list

    def make_gen(self):
        for keyword in self.keyword_list:
            result_list = self.crawling(keyword)
            time.sleep(random.randrange(self.delay_range[0], self.delay_range[1]))
            if result_list is not None:
                yield result_list
            else:
                logger.warn(f'Not found vod. keyword: {keyword}')


class DynamicCrawler:
    def __init__(self, search_option, num, keyword_list, window, timeout=10, retry_delay=1.5, delay_range=(1, 2)):
        self.search_option = SEARCH_OPTION[int(search_option)]
        self.num = num
        self.keyword_list = keyword_list

        # driver option, you must run the code root directory
        # chrome version: 89.0.4389.23
        if window:
            self.chrome_driver_path = os.path.abspath('./chromedrivers/chromedriver.exe')
        else:
            self.chrome_driver_path = os.path.abspath('./chromedrivers/chromedriver')
        self.driver = None
        self.timeout = timeout

        self.search_url = 'https://www.youtube.com/results?'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
        self.retry_delay = retry_delay
        self.delay_range = delay_range

        self._start_driver()

    def _start_driver(self):
        window_size = "1920,1080"
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--window-size=%s" % window_size)
        self.driver = webdriver.Chrome(executable_path=self.chrome_driver_path, chrome_options=chrome_options)

    def close_driver(self):
        self.driver.quit()
        self.driver = None

    def crawling(self, keyword):
        result_list = []
        url = f'{self.search_url}search_query={keyword}&sp={self.search_option}'

        try:
            self.driver.get(url)
            urls = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_all_elements_located((By.ID, 'content')))
        except TimeoutException:
            logger.error('Time out waiting for page to load')
            return None

        body = self.driver.find_element_by_tag_name('body')

        scan = True
        section_list = None
        while scan:
            body.send_keys(Keys.PAGE_DOWN)
            section_list = self.driver.find_elements(By.CSS_SELECTOR, '#contents > ytd-item-section-renderer')
            result_len = 0
            for section in section_list:
                result_len += len(section.find_elements(By.CSS_SELECTOR, '#contents > ytd-video-renderer'))
            if result_len > self.num:
                scan = False
                break

        if section_list is None:
            return None

        for section in section_list:
            videos = section.find_elements(By.CSS_SELECTOR, '#contents > ytd-video-renderer')
            for v in videos:
                element = v.find_element(By.ID, 'video-title')
                video_url = element.get_attribute('href')
                video_id = video_url.replace('https://www.youtube.com/watch?v=', '')
                title = element.get_attribute('title')
                result_dict = {'video_id': video_id,
                               'video_url': video_url,
                               'title': title,
                               'keyword': keyword}
                if len(result_list) < self.num:
                    result_list.append(result_dict)
                else:
                    pass

        return result_list

    def make_gen(self):
        for keyword in self.keyword_list:
            result_list = self.crawling(keyword)
            time.sleep(random.randrange(self.delay_range[0], self.delay_range[1]))
            if result_list is not None:
                yield result_list
            else:
                logger.warn(f'Not found vod. keyword: {keyword}')
