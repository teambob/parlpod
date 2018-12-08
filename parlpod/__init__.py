import os
import itertools
import logging
import os
import shutil
import tempfile

__all__ = ['Amazon', 'Rss', 'DownloadMedia']

from . import Amazon
from . import Rss
from . import DownloadMedia

#import Amazon
#import Rss
#import DownloadMedia

def lambda_handler(event, context):
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    run(os.getenv('BUCKET_NAME'), os.getenv('HTTP_PREFIX'), False, os.getenv('LOG_LEVEL', logging.INFO))

def run(bucketName, httpPrefix, dryRun, logLevel):
    logging.basicConfig(level=logLevel, format='%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    feeds = [
        {'name': 'all', 'url': 'http://parlview.aph.gov.au/browse.php?&rss=1'},
        {'name': 'senate', 'url': 'http://parlview.aph.gov.au/browse.php?&rss=1&tab=senate'},
        {'name': 'house_of_representatives', 'url': 'http://parlview.aph.gov.au/browse.php?&rss=1&tab=hor'},
        {'name': 'committees', 'url': 'http://parlview.aph.gov.au/browse.php?&rss=1&tab=joint_comm'},
        {'name': 'press_conferences', 'url': 'http://parlview.aph.gov.au/browse.php?&rss=1&tab=press_conf'},
        {'name': 'other', 'url': 'http://parlview.aph.gov.au/browse.php?&rss=1&tab=other'},
    ]

    # temp directory
    workingDir = tempfile.mkdtemp(prefix='parlpod')
    # create temp subdirectories
    os.mkdir(os.path.join(workingDir, 'media'))
    os.mkdir(os.path.join(workingDir, 'rss'))


    amazon = Amazon.Amazon(bucketName)
    # Download RSS Feeds
    reader = Rss.RssReader()
    podcastItems = [reader.getTitleAndVideoIds(feed['url']) for feed in feeds]


    # Combine list of video IDs
    videoIds = [item['video_id'] for item in itertools.chain.from_iterable(podcastItems)]
    logging.debug('VideoIDs: %s', ", ".join(videoIds))

    # Check which video IDs have already been downloaded
    missingVideoIds = list(set(videoIds).difference(amazon.checkVideoIds(videoIds)))

    # Download missing video IDs
    logging.info('VideoIds required: %s', ', '.join(videoIds))
    logging.info('VideoIds to download: %s', ', '.join(missingVideoIds))
    client = DownloadMedia.ParlViewClient()
    videoMetadata = {}
    for videoId in videoIds:
        metadata = client.getMetadata(videoId)
        if videoId in missingVideoIds:
            client.download(videoId, metadata['duration'], os.path.join(workingDir, 'media'))
            if not dryRun:
                # Upload media files
                filename = os.path.join(workingDir, 'media', videoId + ".m4a")
                amazon.uploadMedia([filename])
                #TODO: Only remove if lambda
                os.remove(filename)

        videoMetadata[videoId] = metadata

    #TODO: verify date and use modified_date if available
    podcastItems = [[{'title': item['title'], 'video_id': item['video_id'], 'date': videoMetadata[item['video_id']]['created_date']} for item in podcast] for podcast in podcastItems]

    # Generate RSS files
    for podcast in zip(podcastItems, feeds):
        writer = Rss.RssWriter(httpPrefix, os.path.join(workingDir, 'rss'))
        writer.generateFeed(podcast[0], podcast[1]['name'])

    if not dryRun:
        # Upload RSS files
        for feed in feeds:
            amazon.uploadRss(os.path.join(workingDir, 'rss', feed['name']+".xml"))

    # Delete temp directory

    if len(workingDir)>0 and workingDir != '/':
        shutil.rmtree(workingDir)
