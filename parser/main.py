"""Downloads books for deep learning
"""
from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor
import os

import tempfile
import requests
from bs4 import BeautifulSoup
import sys
import zipfile


def get_structure():

    url = "http://www.deeplearningbook.org/"
    data = requests.get(url)
    document = BeautifulSoup(data.text)
    chapters = []

    chapter_list = document.find_all("ul")
    for index, chapter in enumerate(chapter_list):
        if index == 0:
            continue
        print(chapter, end="\n")
        for a in chapter.findAll('a'):
            chapters.append((a.get('href'), a.text))

    return chapters


def get_chapter(chapter):

    chapter_url, chapter_name = chapter
    url = "http://www.deeplearningbook.org/" + chapter_url
    data = requests.get(url)
    return data.text


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


def save_chapter(file_name, file_path, chapter_data):

    path = os.path.join(file_path, file_name + ".html")
    with open(path, 'w', encoding="utf8") as ch_file:
        ch_file.write(chapter_data)

if __name__ == "__main__":

    args = sys.argv[1:]

    path = None
    if args:
        path = args[0]
        if not os.path.exists(path):
            os.makedirs(path)
    else:
        raise AttributeError("no output path specified")

    parser = ArgumentParser()
    parser.add_argument('--dir', '-d', type=str, help='output book dir')
    parser.add_argument('--output', '-o', type=str, help='output book filename', default='book')
    options = parser.parse_args(args)

    chapters = get_structure()

    with ProcessPoolExecutor(max_workers=2) as executor:
        with tempfile.TemporaryDirectory() as tmpdir:
            for chapter, chapter_data in zip(chapters, executor.map(get_chapter, chapters)):
                chapter_url, chapter_name = chapter
                print("load chapter", chapter_name, "from", chapter_url)
                save_chapter(chapter_name.replace(" ", "_"), tmpdir, chapter_data)

            zipf = zipfile.ZipFile(os.path.join(options.dir, options.output), 'w', zipfile.ZIP_DEFLATED)
            zipdir(tmpdir, zipf)
            zipf.close()

    print("success")
