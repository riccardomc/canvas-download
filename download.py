import os
import re
import sys
import unicodedata
from multiprocessing.pool import ThreadPool
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from canvasapi import Canvas

API_KEY = os.getenv("CANVAS_API_KEY")
COURSE_URL = sys.argv[1]
parsed_url = urlparse(COURSE_URL)
API_URL = parsed_url.scheme + "://" + parsed_url.netloc
COURSE_ID = parsed_url.path.split("/")[-1]


def get_page_urls_from_syllabus(syllabus_body):
    """
    Extract only canvas pages from syllabus body

    :param syllabus_body: the HTML body of the syllabus page
    :returns: all links that look like canvas pages
    """
    pages_url = "%s/courses/%s/pages/" % (API_URL, COURSE_ID)
    for url, text in get_links(syllabus_body):
        if pages_url in url:
            yield url.split("/")[-1]


def get_links(body):
    """
    Extract all links from an html body.

    :param body: an HTML document
    :returns: the link url and its title
    """
    soup = BeautifulSoup(body, features="html.parser")
    links = soup.find_all("a")

    for link in links:
        url = link.get("href", None)
        title = link.get("title")
        if title is None:
            title = link.text
        if url is not None:
            yield url, title


def slugify(value, allow_unicode=False):

    """
    Convert spaces or repeated dashes to single dashes. Remove characters that aren't
    alphanumerics, underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.

    Taken from https://github.com/django/django/blob/master/django/utils/text.py

    :param value: input string
    :param allow_unicode: convert to ASCII if 'allow_unicode' is False.
    :returns: the slugified string
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def download(link):
    """
    Download a file from Canvas

    :param link: a tuple containing the url and the destination filename
    :returns: a string representing the result of the download
    """
    url, filename = link[0], link[1]
    if API_URL in url:
        file_id = url.split("/")[-1].split("?")[0]
        print("DOWN:", file_id, filename)
        try:
            canvas_file = canvas.get_file(file_id)
            canvas_file.download(filename)
        except Exception as e:
            return "FAIL: %s %s" % (url, e)
        return "DONE: " + file_id
    else:
        return "SKIP: " + url


def mkdir(dirname):
    """
    Create directory if it doesn't exist

    :param dirname: the directory name
    """
    try:
        os.mkdir(dirname)
    except Exception:
        pass


def get_filename(directory, link_title):
    """
    Generate filename.

    FIXME: We assume the file is a PDF...

    :param directory: the directory part of the filename
    :param link_title: link name
    :returns: a path
    """
    return os.path.join("./", directory, slugify(link_title) + ".pdf")


canvas = Canvas(API_URL, API_KEY)
course = canvas.get_course(COURSE_ID, include="syllabus_body")

something = []
for page_url in get_page_urls_from_syllabus(course.syllabus_body):
    page = course.get_page(page_url)
    directory_name = slugify(page_url)
    for link in get_links(page.body):
        mkdir(page_url)
        filename = get_filename(directory_name, link[1])
        something.append((link[0], filename))

results = ThreadPool(8).imap_unordered(download, something)
for r in results:
    print(r)
