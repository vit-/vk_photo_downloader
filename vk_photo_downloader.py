import requests
import sys
from os import path, makedirs

API_URL = 'https://api.vk.com/method'


class VKException(Exception):
    pass


def request_api(method, params={}):
    response = requests.get('{}/{}'.format(API_URL, method), params=params)
    data = response.json()
    if 'error' in data:
        raise VKException('Code - {error_code}. Message - {error_msg}'.format(
            **data['error']))
    return data['response']


def create_parser():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('group', help='Owner name or id')
    parser.add_argument('-a', '--album', type=int,
                        help='Specify album id to download')
    parser.add_argument('-p', '--path',
                        help='Specify path to save photos',
                        default=path.join(path.dirname(path.abspath(__file__)),
                                          'download/'))
    return parser


def get_download_dir(dir_path):
    abs_path = path.abspath(dir_path)
    if not path.exists(abs_path):
        makedirs(abs_path)
    return abs_path


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()

    try:
        group_info = request_api(
            'groups.getById',
            params={'group_id': args.group}
        )[0]
    except VKException:
        print('Can\'t find group with name {}'.format(args.group))
    else:
        gid = group_info['gid']
        albums = request_api(
            'photos.getAlbums',
            params={'owner_id': '-{}'.format(gid)}
        )
        download_dir = get_download_dir(args.path)
        print('Saving to {}...'.format(download_dir))
        if args.album:
            valid = False
            for album in albums:
                if args.album == album['aid']:
                    valid = True
                    break
            if valid:
                photos = request_api(
                    'photos.get',
                    params={'owner_id': '-{}'.format(gid),
                            'album_id': args.album}
                )
                photos_count = len(photos)
                pos_len = len(str(photos_count))
                for pos_raw, photo in enumerate(photos):
                    sys.stdout.write('\rDownloading {} of {}'.format(
                        pos_raw + 1, photos_count))
                    sys.stdout.flush()

                    try:
                        photo_url = photo['src_xxbig']
                    except KeyError:
                        continue
                    else:
                        response = requests.get(photo['src_xxbig'], stream=True)
                        ext = photo_url.split('.')[-1]
                        pos = str(pos_raw + 1).rjust(pos_len, '0')
                        with open('{}/{}.{}'.format(download_dir, pos, ext), 'wb') as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                print('\n')
            else:
                print('Wrong album id')
        else:
            print('Album list\n\nid\t\ttitle')
            print('-' * 80)
            for album in albums:
                print(u'{aid}\t{title}'.format(**album))
