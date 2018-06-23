from lxml import etree
import logging
import random
import requests
import os
import time


def download(videoId, directory='.'):
    # ts2 seems unnecessary
    metadataResponse = requests.get('http://parlview.aph.gov.au/player/config5.php?siteID=1&videoID={videoId}&profileIdx=30&ts2=1528111836852'.format(videoId=videoId))
    root = etree.fromstring(metadataResponse.content)
    duration = root.find('playlist/media/info/duration').text
    created_date = root.find('playlist/module/media_area/type/bookmark/created')

    random.seed()
    trimId = random.randrange(2**32)

    logging.debug("Duration: {duration}".format(duration=duration))
    requests.get('http://download.parlview.aph.gov.au/downloads/trimAjax.php?mux=0&siteID=1&type=mp4_aud&videoID={videoId}&from=0&to={duration}&R={trimId}'.format(videoId=videoId, duration=duration, trimId=trimId))
    #time.sleep(61)
    #R=random value. Must match trim request???
    #video id
    #duration from XML in previous request
    download = None
    while True:
        logging.info("Downloading")
        try:
            download = requests.get('http://download.parlview.aph.gov.au/downloads/trim.php?mux=0&siteID=1&type=mp4_aud&videoID={videoId}&from=0&to={duration}&R={trimId}&action=directDownload'.format(videoId=videoId, duration=duration, trimId=trimId))
        except requests.exceptions.BaseHTTPError as e:
            logging.warning(e.message)

        if len(download.content) > 0:
            break
        logging.info("Retrying")
        time.sleep(1)

    logging.debug(download.status_code)
    with open(os.path.join(directory, "%s.m4a"%videoId), 'wb') as f:
        f.write(download.content)
        f.close()

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    download(videoId=399774)