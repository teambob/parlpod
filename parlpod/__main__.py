import argparse
from __init__ import run


if __name__=='__main__':
    # configuration
    parser = argparse.ArgumentParser()

    parser.add_argument('--bucket', required=True)
    parser.add_argument('--http-prefix', required=True)
    parser.add_argument('--dry-run', action='store_true')

    options = parser.parse_args()

    run(options.bucket, options.http_prefix, options.dry_run)
