import itertools
import logging
import argparse
import os
import tempfile

import Amazon
import DownloadMedia
import Rss

logging.basicConfig(level=logging.DEBUG)
feeds = [('all', 'http://parlview.aph.gov.au/browse.php?&rss=1')]

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
podcastItems = [Rss.getTitleAndVideoIds(feed[1]) for feed in feeds]
# Combine list of video IDs
videoIds = [item[1] for item in itertools.chain.from_iterable(podcastItems)]
logging.debug('VideoIDs: %s', ", ".join(videoIds))

# Check which video IDs have already been downloaded
# TODO: where will this data be stored?
missingVideoIds = videoIds

# Download missing video IDs
logging.debug('Downloading: %s', ", ".join(videoIds))
for videoId in missingVideoIds:
    DownloadMedia.download(videoId, os.path.join(workingDir, 'media'))

# Generate RSS files
for podcast in zip(podcastItems, feeds):
    Rss.generateFeed(podcast[0], httpPrefix, podcast[1][0], os.path.join(workingDir, 'rss'))

if not options.dry_run:
    # Upload media files
    amazon.uploadMedia([os.path.join(workingDir, 'media', videoId+".m4a") for videoId in videoIds])

    # Upload RSS files
    for feed in feeds:
        amazon.uploadRss(os.path.join(workingDir, 'rss', feed[0]+".xml"))

# TODO: Delete temp directory