import argparse

from operations import (
    init,
    download,
    upload,
    abandon,
    LOWER_LIMIT,
    UPPER_LIMIT
)

if __name__ == "__main__":

    # how i want to use the tool:
    # python3 cli.py init --config /path/to/config.ini
    # python3 cli.py download --num-images 40
    # python3 cli.py upload
    # python3 cli.py abandon
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'operation',
        choices=['init', 'download', 'upload', 'abandon']
    )

    parser.add_argument('-n', '--num-images', type=int)

    parser.add_argument('-c', '--config')

    args = parser.parse_args()

    operation = args.operation

    if operation == 'init':
        init(args.config)
    elif operation == 'download':
        download(args.num_images)
    elif operation == 'upload':
        upload()
    else:
        abandon()
