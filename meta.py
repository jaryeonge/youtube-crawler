import requests
import json
import time
import unicodedata
from tqdm import tqdm


class MetaCrawler:
    def __init__(self, api_key_list: list):
        self.api_key_list = api_key_list
        self.url = 'https://www.googleapis.com/youtube/v3/videos?'

    def crawling_meta(self, video_id: str):
        url = 'https://www.googleapis.com/youtube/v3/videos?'
        if self.api_key_list == []:
            print('Total quota has been exceeded')
            return 'end'
        else:
            api_key = self.api_key_list[0]
        params = {'part': 'snippet, contentDetails, statistics',
                  'id': video_id,
                  'key': api_key}
        try:
            response = requests.get(url=url, params=params)
        except Exception as e:
            print("error: ", e)
            return 'error'

        if response.status_code == 403:
            error = response.json()['error']['errors'][0]['reason']
            if error == 'forbidden':
                print(response.json()['error']['errors'][0]['message'])
                return 'forbidden'
            elif error == 'quotaExceeded':
                print(f"{api_key}'s quota has been exceeded")
                return 'exceeded'
            else:
                print(response.text)
                return 'error'

        try:
            res_json = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            try:
                time.sleep(0.1)
                response = requests.get(url=url, params=params)
                res_json = json.loads(response.text)
            except Exception as e:
                print("error: ", e)
                return None

        try:
            snippet = res_json['items'][0]['snippet']
        except IndexError:
            print("video id:", video_id, "status: ", response.status_code, "\n", "json:", res_json)
            return 'not exist'

        snippet = res_json['items'][0]['snippet']
        content_details = res_json['items'][0]['contentDetails']
        statistics = res_json['items'][0]['statistics']

        result_dict = {}

        # 세부정보가 존재하지 않을 경우, 빈 값 처리
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

    def make_gen(self, id_list: list):
        for video_id in tqdm(id_list, desc='crawling meta data'):
            result = self.crawling_meta(video_id)
            if result == 'end':
                break
            elif result == 'forbidden':
                break
            elif result == 'exceeded':
                result = self.crawling_meta(video_id)
                if result == 'end':
                    break
                elif result == 'forbidden':
                    break
            yield result, video_id
