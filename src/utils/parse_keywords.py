import csv
from utils.crawling_logger import default_logger

logger = default_logger()


def extract_keywords(path: str):
    keyword_list = []
    if path.endswith('.txt'):
        with open(path, 'r') as f:
            while True:
                line = f.read()
                if not line:
                    break
                keyword_list.append(line)

    elif path.endswith('.csv'):
        with open(path, 'r') as f:
            reader = csv.reader(f)
            for keyword in reader:
                keyword_list.append(keyword[0])
    else:
        logger.error('When loading keywords, error occurred: This program only supports csv and txt')
        raise ValueError('This program only supports csv and txt')

    return keyword_list
