"""Downloads books for deep learning
"""
from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor
import os

import logging
import tempfile
import requests
from bs4 import BeautifulSoup
import sys
import zipfile
import time


def get_structure():

    url = "http://www.deeplearningbook.org/"
    data = requests.get(url)
    document = BeautifulSoup(data.text)
    chapters = []

    chapter_list = document.find_all("ul")
    for index, chapter in enumerate(chapter_list):
        if index == 0:
            continue
        for a in chapter.findAll('a'):
            chapters.append((a.get('href'), a.text))

    return chapters


def get_chapter(chapter):

    chapter_url, chapter_name = chapter
    url = "http://www.deeplearningbook.org/" + chapter_url
    data = requests.get(url)
    return data.text


def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


def save_chapter(file_name, file_path, chapter_data):

    path = os.path.join(file_path, file_name + ".html")
    with open(path, 'w', encoding="utf8") as ch_file:
        ch_file.write(chapter_data)

logger = None


def createLogger(filename, loglevel):
    global logger
    FORMAT = "%(asctime)-15s"
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger(__name__)
    logger.setLevel(loglevel)
    logger.addHandler(logging.FileHandler(filename, mode="w"))
    logger.addHandler(logging.StreamHandler())


if __name__ == "__main__":

    args = sys.argv[1:]

    parser = ArgumentParser()
    parser.add_argument('--dir', '-d', type=str, help='output book dir')
    parser.add_argument('--output', '-o', type=str, help='output book filename', default='book')
    parser.add_argument('--workers', '-w', type=int, help="workers to download", default=10)
    parser.add_argument('--logfile', '-l', type=str, help="name of logfile", default=__file__.replace(".py", ".log"))
    parser.add_argument('--loglevel', '-v', type=str, help="", default=logging.DEBUG)
    options = parser.parse_args(args)

    createLogger(options.logfile, options.loglevel)

    path = options.dir
    if not os.path.exists(path):
        os.makedirs(path)
        logger.debug("create dir to upload = %s", path)

    chapters = get_structure()
    logger.debug("start downloading %d files, workers = %d", len(chapters), options.workers)

    begin = time.time()
    with ProcessPoolExecutor(max_workers=options.workers) as executor:
        with tempfile.TemporaryDirectory() as tmpdir:
            for chapter, chapter_data in zip(chapters, executor.map(get_chapter, chapters)):
                chapter_url, chapter_name = chapter
                logger.debug("load chapter => name=%-40s, url=%s", chapter_name, chapter_url)
                save_chapter(chapter_name.replace(" ", "_"), tmpdir, chapter_data)

            zipf = zipfile.ZipFile(os.path.join(options.dir, options.output + ".zip"), 'w', zipfile.ZIP_DEFLATED)
            zipdir(tmpdir, zipf)
            zipf.close()
    end = time.time()
    logger.debug("success -> time consumed = %d seconds", end - begin)
