import requests
import json
import time
import unicodedata

from utils.crawling_logger import default_logger

logger = default_logger()


class MetaCrawler:
    def __init__(self, api_key_list: list):
        self.api_key_list = api_key_list
        self.api_key = self.api_key_list.pop(0)
        self.url = 'https://www.googleapis.com/youtube/v3/videos?'

    def request_data(self, video_id, api_key):
        params = {'part': 'snippet, contentDetails, statistics',
                  'id': video_id,
                  'key': api_key}

        response = requests.get(url=self.url, params=params)
        return response

    def error_checking(self, response):
        if response.status_code == 403:
            error = response.json()['error']['errors'][0]['reason']
            if error == 'forbidden':
                logger.error(response.json()['error']['errors'][0]['message'])
                return 'forbidden'
            elif error == 'quotaExceeded':
                logger.warn(f"{self.api_key}'s quota has been exceeded")
                return 'exceeded'
            else:
                logger.error(response.text)
                return 'error'
        else:
            return 'ok'

    def crawling_meta(self, video_id: str, keyword: str):
        response = self.request_data(video_id, self.api_key)
        status = self.error_checking(response)
        if status == 'exceeded':
            while True:
                if not self.api_key_list:
                    logger.info('Total quota has been exceeded')
                    return 'end'
                self.api_key = self.api_key_list.pop(0)
                response = self.request_data(video_id, self.api_key)
                status = self.error_checking(response)
                if status != 'exceeded':
                    break

        if status == 'ok':
            pass
        else:
            return None

        try:
            res_json = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            return None

        try:
            snippet = res_json['items'][0]['snippet']
        except IndexError:
            logger.error("video id:", video_id, "status: ", response.status_code, "\n", "json:", res_json)
            return None

        snippet = res_json['items'][0]['snippet']
        content_details = res_json['items'][0]['contentDetails']
        statistics = res_json['items'][0]['statistics']

        result_dict = {'keyword': keyword}

        # snippet
        try:
            result_dict['channel_id'] = snippet['channelId']
        except KeyError:
            result_dict['channel_id'] = ''

        try:
            result_dict['channel_title'] = snippet['channelTitle']
        except KeyError:
            result_dict['channel_title'] = ''
        try:
            title = snippet['title']
            title = str(title)
            title = unicodedata.normalize('NFC', title)  # 자음 모음 분리현상 해결
            result_dict['title'] = title
        except KeyError:
            result_dict['title'] = ''
        try:
            description = snippet['description']
            description = str(description)
            description = unicodedata.normalize('NFC', description)  # 자음 모음 분리현상 해결
            result_dict['description'] = description
        except KeyError:
            result_dict['description'] = ''
        try:
            result_dict['thumbnail'] = snippet['thumbnails']['high']['url']  # options: default/medium/high/standard/maxres
        except KeyError:
            result_dict['thumbnail'] = ''
        try:
            result_dict['tags'] = ','.join(snippet['tags'])
        except KeyError:
            result_dict['tags'] = ''
        try:
            result_dict['publishedAt'] = snippet['publishedAt']
        except KeyError:
            result_dict['publishedAt'] = ''

        # contentDetails
        try:
            result_dict['duration'] = content_details['duration'].replace('PT', '')
        except KeyError:
            result_dict['duration'] = ''
        try:
            result_dict['licensed'] = str(content_details['licensedContent'])
        except KeyError:
            result_dict['licensed'] = ''

        # statistics
        try:
            result_dict['view_count'] = statistics['viewCount']
        except KeyError:
            result_dict['view_count'] = ''
        try:
            result_dict['like_count'] = statistics['likeCount']
        except KeyError:
            result_dict['like_count'] = ''
        try:
            result_dict['dislike_count'] = statistics['dislikeCount']
        except KeyError:
            result_dict['dislike_count'] = ''
        try:
            result_dict['favorite_count'] = statistics['favoriteCount']
        except KeyError:
            result_dict['favorite_count'] = ''
        try:
            result_dict['comment_count'] = statistics['commentCount']
        except KeyError:
            result_dict['comment_count'] = ''

        return result_dict
