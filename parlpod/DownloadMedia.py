from lxml import etree
import dateutil.parser
import logging
import random
import requests
import os
import time


class ParlViewClient:
    def getMetadata(self, videoId):
        # ts2 seems unnecessary
        metadataResponse = requests.get(
            'https://parlview.aph.gov.au/player/config5.php?siteID=1&videoID={videoId}&profileIdx=30&ts2=1528111836852'.format(
                videoId=videoId))
        root = etree.fromstring(metadataResponse.content)
        duration = root.findtext('playlist/media/info/duration', '')
        created_date = dateutil.parser.parse(root.find('playlist/media/module/media_area/bookmark/created').text)
        modified_date = dateutil.parser.parse(
            root.findtext('playlist/media/module/media_area/bookmark/modified', created_date))
        return {'duration': duration, 'created_date': created_date, 'modified_date': modified_date}

    def download(self, videoId, duration, directory='.'):
        logging.info("Downloading videoId: %s", videoId)

        random.seed()
        trimId = random.randrange(2 ** 32)

        logging.debug("Duration: {duration}".format(duration=duration))
        requests.get(
            'https://download-parlview.aph.gov.au/downloads/trimAjax.php?mux=0&siteID=1&type=mp4_aud&videoID={videoId}&from=0&to={duration}&R={trimId}'.format(
                videoId=videoId, duration=duration, trimId=trimId))
        # time.sleep(61)
        # R=random value. Must match trim request???
        # video id
        # duration from XML in previous request
        download = None
        while True:
            try:
                download = requests.get(
                    'https://download-parlview.aph.gov.au/downloads/trim.php?mux=0&siteID=1&type=mp4_aud&videoID={videoId}&from=0&to={duration}&R={trimId}&action=directDownload'.format(
                        videoId=videoId, duration=duration, trimId=trimId))
            except requests.exceptions.RequestException as e:
                logging.warning(e)

            if len(download.content) > 0:
                break
            logging.info("Retrying")
            time.sleep(1)

        logging.debug(download.status_code)
        with open(os.path.join(directory, "%s.m4a" % videoId), 'wb') as f:
            f.write(download.content)
            f.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    client = ParlViewClient()
    #metadata = client.getMetadata(videoId=399774)
    client.download(videoId=399774, duration=9999999)
