import boto3
import os

class Amazon:
    def __init__(self, bucketName):
        self.s3 = boto3.client("s3")
        self.bucketName = bucketName


    def checkVideoIds(self, videoIds):
        return videoIds


    def uploadMedia(self, filenames):
        for filename in filenames:
            self.s3.upload_file(Filename=filename, Bucket=self.bucketName, Key='media/{basename}'.format(basename=os.path.basename(filename)))

    def uploadRss(self, filename):
        self.s3.upload_file(Filename=filename, Bucket=self.bucketName, Key='rss/{basename}'.format(basename=os.path.basename(filename)))