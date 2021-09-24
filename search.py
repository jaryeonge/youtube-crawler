import os
import requests
import re
import json
import time
import random
from tqdm import tqdm
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys


class StaticCrawler:
    def __init__(self):
        # search filter
        self.sp_option = {'동영상+모두+관련성': 'EgIQAQ%3D%3D',
                          '동영상+모두+업로드날짜': 'CAISAhAB',
                          '동영상+모두+조회수': 'CAMSAhAB',
                          '동영상+모두+평점': 'CAESAhAB',
                          '동영상+이번달+관련성': 'EgQIBBAB',
                          '동영상+이번달+업로드날짜': 'CAISBAgEEAE%3D',
                          '동영상+이번달+조회수': 'CAMSBAgEEAE%3D',
                          '동영상+이번달+평점': 'CAESBAgEEAE%3D',
                          '동영상+올해+관련성': 'EgQIBRAB',
                          '동영상+올해+업로드날짜': 'CAISBAgFEAE%3D',
                          '동영상+올해+조회수': 'CAMSBAgFEAE%3D',
                          '동영상+올해+평점': 'CAESBAgFEAE%3D'}
        self.search_url = 'https://www.youtube.com/results?'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
        self.retry_delay = 1.5
        self.delay_range = (1, 3)

    def crawling(self, keyword, option='동영상+모두+관련성'):
        params = {'search_query': keyword,
                  'sp': self.sp_option[option]}
        result_list = []

        # request
        try:
            response = requests.get(url=self.search_url, params=params, headers=self.headers)
        except Exception as e:
            print(e)
            print('retry...')
            time.sleep(self.retry_delay)
            try:
                response = requests.get(url=self.search_url, params=params, headers=self.headers)
            except Exception as e:
                print(e)
                return None

        # parsing
        try:
            res_text = response.text
            compiler = re.compile(r'ytInitialData\s*=\s*(\{.*?\});')

            res_yt = compiler.findall(res_text)
            res_json = json.loads(res_yt[0])
            res_section = res_json['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
        except KeyError as e:
            print(e)
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
            print('there is no content')
            return None

        for item in items:
            try:
                info = item['videoRenderer']

                video_id = info['videoId']
                video_url = f'https://www.youtube.com/watch?v={video_id}'
                title = info['title']['runs'][0]['text']

                result_dict = {'video_id': video_id,
                               'video_url': video_url,
                               'title': title}
                result_list.append(result_dict)

            except KeyError:
                print('ad!')
                continue

        return result_list

    def make_gen(self, keyword_list: list, option='동영상+모두+관련성'):
        for keyword in tqdm(keyword_list, desc='crawling ids'):
            result_list = self.crawling(keyword, option)
            time.sleep(random.randrange(self.delay_range[0], self.delay_range[1]))
            if result_list is not None:
                yield result_list
            else:
                print(f'{keyword} was not crawled')


class DynamicCrawler:
    def __init__(self, window=True, timeout=10, retry_delay=1.5, delay_range=(1, 2), max_result=100):
        # driver option, you must run the code inside the yt_crawler directory
        # chrome version: 89.0.4389.23
        if window:
            self.chrome_driver_path = os.path.abspath('chromedriver.exe')
        else:
            self.chrome_driver_path = os.path.abspath('chromedriver')
        self.driver = None
        self.timeout = timeout

        # youtube option
        self.sp_option = {'동영상+모두+관련성': 'EgIQAQ%3D%3D',
                          '동영상+모두+업로드날짜': 'CAISAhAB',
                          '동영상+모두+조회수': 'CAMSAhAB',
                          '동영상+모두+평점': 'CAESAhAB',
                          '동영상+이번달+관련성': 'EgQIBBAB',
                          '동영상+이번달+업로드날짜': 'CAISBAgEEAE%3D',
                          '동영상+이번달+조회수': 'CAMSBAgEEAE%3D',
                          '동영상+이번달+평점': 'CAESBAgEEAE%3D',
                          '동영상+올해+관련성': 'EgQIBRAB',
                          '동영상+올해+업로드날짜': 'CAISBAgFEAE%3D',
                          '동영상+올해+조회수': 'CAMSBAgFEAE%3D',
                          '동영상+올해+평점': 'CAESBAgFEAE%3D'}
        self.search_url = 'https://www.youtube.com/results?'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
        self.retry_delay = retry_delay
        self.delay_range = delay_range
        self.max_result = max_result

    def start_driver(self):
        CHROMEDRIVER_PATH = self.chrome_driver_path
        WINDOW_SIZE = "1920,1080"

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
        self.driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                                       chrome_options=chrome_options)

    def close_driver(self):
        self.driver.quit()
        self.driver = None

    def crawling(self, keyword, option='동영상+모두+관련성'):
        result_list = []
        if self.driver is None:
            print('please start your chromedriver \nexample: self.start_driver()')
            return None
        url = f'{self.search_url}search_query={keyword}&sp={self.sp_option[option]}'
        try:
            self.driver.get(url)
            urls = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_all_elements_located((By.ID, 'content')))
        except TimeoutException:
            print('Time out waiting for page to load')
            return None

        body = self.driver.find_element_by_tag_name('body')

        scan = True
        while scan:
            body.send_keys(Keys.PAGE_DOWN)
            section_list = self.driver.find_elements(By.CSS_SELECTOR, '#contents > ytd-item-section-renderer')
            result_len = 0
            for section in section_list:
                result_len += len(section.find_elements(By.CSS_SELECTOR, '#contents > ytd-video-renderer'))
            if result_len > self.max_result:
                scan = False
                break

        for section in section_list:
            videos = section.find_elements(By.CSS_SELECTOR, '#contents > ytd-video-renderer')
            for v in videos:
                element = v.find_element(By.ID, 'video-title')
                video_url = element.get_attribute('href')
                video_id = video_url.replace('https://www.youtube.com/watch?v=', '')
                title = element.get_attribute('title')
                result_dict = {'video_id': video_id,
                               'video_url': video_url,
                               'title': title}
                if len(result_list) < self.max_result:
                    result_list.append(result_dict)
                else:
                    pass

        return result_list

    def make_gen(self, keyword_list: list, option='동영상+모두+관련성'):
        if self.driver is None:
            print('please start your chromedriver \nexample: self.start_driver()')
            return None
        for keyword in tqdm(keyword_list, desc='crawling ids'):
            result_list = self.crawling(keyword, option)
            time.sleep(random.randrange(self.delay_range[0], self.delay_range[1]))
            if result_list is not None:
                yield result_list
            else:
                print(f'{keyword} was not crawled')