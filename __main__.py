import itertools
import logging
import argparse
import os
import tempfile

import Amazon
import DownloadMedia
import Rss

logging.basicConfig(level=logging.DEBUG)
feeds = [{'name':'all', 'url':'http://parlview.aph.gov.au/browse.php?&rss=1'}]

# temp directory
workingDir = tempfile.mkdtemp(prefix='parlpod')
# create temp subdirectories
os.mkdir(os.path.join(workingDir, 'media'))
os.mkdir(os.path.join(workingDir, 'rss'))

# configuration
parser = argparse.ArgumentParser()

parser.add_argument('--bucket', required=True)
parser.add_argument('--http-prefix', required=True)
parser.add_argument('--dry-run', action='store_true')

options = parser.parse_args()

bucketName = options.bucket
httpPrefix = options.http_prefix



amazon = Amazon.Amazon(bucketName)
# Download RSS Feeds
reader = Rss.RssReader()
podcastItems = [reader.getTitleAndVideoIds(feed['url']) for feed in feeds]


# Combine list of video IDs
videoIds = [item[1] for item in itertools.chain.from_iterable(podcastItems)]
logging.debug('VideoIDs: %s', ", ".join(videoIds))

# Check which video IDs have already been downloaded
# TODO: where will this data be stored?
missingVideoIds = videoIds

# Download missing video IDs
logging.debug('Downloading: %s', ", ".join(videoIds))
client = DownloadMedia.ParlViewClient()
videoMetadata = {}
for videoId in missingVideoIds:
    metadata = client.getMetadata(videoId)
    client.download(videoId, metadata['duration'], os.path.join(workingDir, 'media'))
    videoMetadata[videoId] = metadata

#TODO: verify date and use modified_date if available
podcastItems = [[{'title': item['title'], 'video_id': item['video_id'], 'date': videoMetadata[item['video_id']]['created_date']} for item in podcast] for podcast in podcastItems]

# Generate RSS files
for podcast in zip(podcastItems, feeds):
    writer = Rss.RssWriter(httpPrefix, os.path.join(workingDir, 'rss'))
    writer.generateFeed(podcast[0], podcast[1]['name'])

if not options.dry_run:
    # Upload media files
    amazon.uploadMedia([os.path.join(workingDir, 'media', videoId+".m4a") for videoId in videoIds])

    # Upload RSS files
    for feed in feeds:
        amazon.uploadRss(os.path.join(workingDir, 'rss', feed['name']+".xml"))

# TODO: Delete temp directory