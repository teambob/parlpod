import base64
import datetime

import bson
import itertools
import logging
import os
import shutil
import tempfile

__all__ = ['Amazon', 'Rss', 'DownloadMedia']

from . import Amazon
from . import Rss
from . import DownloadMedia


def lambda_handler(event, context):
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    parlpod = Parlpod(os.getenv('BUCKET_NAME'), os.getenv('HTTP_PREFIX'), os.getenv('LOG_LEVEL', logging.INFO), False)
    parlpod.run()


def lambda_get_list(event, context):
    parlpod = Parlpod(os.getenv('BUCKET_NAME'), os.getenv('HTTP_PREFIX'), os.getenv('LOG_LEVEL', logging.INFO), False)
    (podcastItems, missingVideoIds, videoMetadata) = parlpod.getList()
    return {'state': base64.b64encode(bson.dumps({'podcastItems': podcastItems, 'missingVideoIds': missingVideoIds, 'videoMetadata': videoMetadata})).decode('ASCII')}


def lambda_download(event, context):
    state = bson.loads(base64.b64decode(event['state'].encode('ASCII')))
    if len(state['missingVideoIds'])==0:
        return {'done': True, 'state': base64.b64encode(bson.dumps(state)).decode('ASCII')}

    missingVideoId = state['missingVideoIds'].pop()
    parlpod = Parlpod(os.getenv('BUCKET_NAME'), os.getenv('HTTP_PREFIX'), os.getenv('LOG_LEVEL', logging.INFO), False)
    parlpod.createTemp()
    parlpod.copyMedia(missingVideoId, state['videoMetadata'][missingVideoId])
    parlpod.deleteTemp()

    return {'done': len(state['missingVideoIds'])==0, 'state': base64.b64encode(bson.dumps(state)).decode('ASCII')}

def lambda_create_rss(event, context):
    state = bson.loads(base64.b64decode(event['state'].encode('ASCII')))
    parlpod = Parlpod(os.getenv('BUCKET_NAME'), os.getenv('HTTP_PREFIX'), os.getenv('LOG_LEVEL', logging.INFO), False)
    parlpod.createTemp()
    parlpod.createRss(state['podcastItems'], state['videoMetadata'])
    parlpod.deleteTemp()


class Parlpod:
    def __init__(self, bucketName, httpPrefix, logLevel, dryRun):
        self.dryRun = dryRun
        root = logging.getLogger()
        if root.handlers:
            for handler in root.handlers:
                root.removeHandler(handler)
        logging.basicConfig(level=logLevel, format='%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

        self.feeds = [
            {'name': 'all', 'url': 'http://parlview.aph.gov.au/browse.php?&rss=1'},
            {'name': 'senate', 'url': 'http://parlview.aph.gov.au/browse.php?&rss=1&tab=senate'},
            {'name': 'house_of_representatives', 'url': 'http://parlview.aph.gov.au/browse.php?&rss=1&tab=hor'},
            {'name': 'committees', 'url': 'http://parlview.aph.gov.au/browse.php?&rss=1&tab=joint_comm'},
            {'name': 'press_conferences', 'url': 'http://parlview.aph.gov.au/browse.php?&rss=1&tab=press_conf'},
            {'name': 'other', 'url': 'http://parlview.aph.gov.au/browse.php?&rss=1&tab=other'},
        ]
        self.client = DownloadMedia.ParlViewClient()
        self.amazon = Amazon.Amazon(bucketName)
        self.httpPrefix = httpPrefix

    def run(self):
        self.createTemp()
        (podcastItems, missingVideoIds, videoMetadata) = self.getList()
        for videoId in missingVideoIds:
            self.copyMedia(videoId, videoMetadata[videoId])
        self.createRss(podcastItems, videoMetadata)
        self.deleteTemp()

    def createTemp(self):
        # temp directory
        self.workingDir = tempfile.mkdtemp(prefix='parlpod')
        # create temp subdirectories
        os.mkdir(os.path.join(self.workingDir, 'media'))
        os.mkdir(os.path.join(self.workingDir, 'rss'))

    def deleteTemp(self):
        # Delete temp directory
        if len(self.workingDir) > 0 and self.workingDir != '/':
            shutil.rmtree(self.workingDir)

    def getList(self):
        # Download RSS Feeds
        reader = Rss.RssReader()
        podcastItems = [reader.getTitleAndVideoIds(feed['url']) for feed in self.feeds]

        # Combine list of video IDs
        videoIds = [item['video_id'] for item in itertools.chain.from_iterable(podcastItems)]
        logging.debug('VideoIDs: %s', ", ".join(videoIds))

        # Check which video IDs have already been downloaded
        missingVideoIds = list(set(videoIds).difference(self.amazon.checkVideoIds(videoIds)))

        # Download missing video IDs
        logging.info('%i VideoIds required: %s', len(videoIds),', '.join(videoIds))
        logging.info('%i VideoIds to download: %s', len(missingVideoIds), ', '.join(missingVideoIds))

        videoMetadata = {videoId: self.client.getMetadata(videoId) for videoId in videoIds}
        skipVideoIds = [ videoId for videoId in videoIds if videoMetadata[videoId]['duration'] and videoMetadata[videoId]['created_date']<datetime.datetime.now()-datetime.timedelta(days=30)]
        logging.info('Skipping %i VideoIds: %s', len(skipVideoIds), ', '.join(skipVideoIds))
        return ([[item for item in feed if item['video_id'] not in skipVideoIds] for feed in podcastItems], [id for id in missingVideoIds if id not in skipVideoIds], videoMetadata)

    def copyMedia(self, videoId, videoMetadata):
        self.client.download(videoId, videoMetadata['duration'], os.path.join(self.workingDir, 'media'))
        if not self.dryRun:
            # Upload media files
            filename = os.path.join(self.workingDir, 'media', videoId + ".m4a")
            self.amazon.uploadMedia([filename])
            # TODO: Only remove if lambda
            os.remove(filename)

    def createRss(self, podcastItems, videoMetadata):
        #TODO: verify date and use modified_date if available
        podcastItems = [[{'title': item['title'], 'video_id': item['video_id'], 'date': videoMetadata[item['video_id']]['created_date']} for item in podcast] for podcast in podcastItems]

        # Generate RSS files
        for podcast in zip(podcastItems, self.feeds):
            writer = Rss.RssWriter(self.httpPrefix, os.path.join(self.workingDir, 'rss'))
            writer.generateFeed(podcast[0], podcast[1]['name'])

        if not self.dryRun:
            # Upload RSS files
            for feed in self.feeds:
                self.amazon.uploadRss(os.path.join(self.workingDir, 'rss', feed['name']+".xml"))
