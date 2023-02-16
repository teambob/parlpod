from bs4 import BeautifulSoup
import dateutil.parser
import logging
import random
import re
import requests
import os
import time


class ParlViewClient:
    def getMetadata(self, videoId):

        metadataResponse = requests.get("https://parlview.aph.gov.au/mediaPlayer.php?videoID={videoId}".format(videoId=videoId))
        metadataHtml = BeautifulSoup(metadataResponse.text, 'html.parser')
        descriptionParagraphs = metadataHtml.select(".tag-description p")
        descriptionParagraphTexts = [descriptionParagraph.get_text().replace("\n", "") for descriptionParagraph in descriptionParagraphs]
        duration = next(match for descriptionParagraphText in descriptionParagraphTexts if (match := re.match(r'^\s*Duration:.*([0-9:]{8}).*$', descriptionParagraphText)))
        if "currently being recorded" in duration.group(0):
            duration = None
        else:
            duration = dateutil.parser.parse(duration.group(1))

        created_date = dateutil.parser.parse(next(match.group(1) for descriptionParagraphText in descriptionParagraphTexts if (match := re.match(r'^\s*Record Datetime:\s*(.*)\s*$', descriptionParagraphText))))
        modified_date = created_date


        return {'duration': duration, 'created_date': created_date, 'modified_date': modified_date}

    def download(self, videoId, duration, directory='.'):
        logging.info("Downloading videoId: %s", videoId)

        random.seed()
        trimId = random.randrange(2 ** 16)
        duration = 999999

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
                time.sleep(1)
                download = requests.get(
                    'https://download-parlview.aph.gov.au/downloads/trim.php?mux=0&siteID=1&type=mp4_aud&videoID={videoId}&from=0&to={duration}&R={trimId}&action=directDownload'.format(
                        videoId=videoId, duration=duration, trimId=trimId))
            except requests.exceptions.RequestException as e:
                logging.warning(e)

            if len(download.content) > 0 and download.headers['content-type'] == 'audio/m4a':
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
