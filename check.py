import requests
import json
import time
from tqdm import tqdm


class Checker:
    def __init__(self, api_key_list: list):
        self.api_key_list = api_key_list
        self.url = 'https://www.googleapis.com/youtube/v3/videos?'

    def check(self, video_id: str):
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
            return 'exist'
        except IndexError:
            print("video id:", video_id, "status: ", response.status_code, "\n", "json:", res_json)
            return 'not exist'

    def make_gen(self, id_list: list):
        for video_id in tqdm(id_list, desc='check youtube contents'):
            result = self.check(video_id)
            if result == 'end':
                break
            elif result == 'forbidden':
                break
            elif result == 'exceeded':
                result = self.check(video_id)
                if result == 'end':
                    break
                elif result == 'forbidden':
                    break
            yield result, video_id