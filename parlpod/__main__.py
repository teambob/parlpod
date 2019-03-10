import argparse
import logging
from . import Parlpod

if __name__=='__main__':
    # configuration
    parser = argparse.ArgumentParser()

    parser.add_argument('--bucket', required=True)
    parser.add_argument('--http-prefix', required=True)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--log-level', default=logging.INFO)

    options = parser.parse_args()

    parlpod = Parlpod(options.bucket, options.http_prefix, options.dry_run, options.log_level)
    parlpod.run()
