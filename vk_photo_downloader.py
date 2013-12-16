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
    parser.add_argument('-a', '--album',
                        help='Specify album id to download')
    parser.add_argument('-p', '--path',
                        help='Specify path to save photos',
                        default=path.join(path.dirname(path.abspath(__file__)),
                                          'download/'))
    return parser


def get_download_dir(dir_path, subdir=None):
    abs_path = path.abspath(dir_path)
    if not subdir is None:
        abs_path = path.join(abs_path, subdir)
    if not path.exists(abs_path):
        makedirs(abs_path)
    return abs_path


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    albums_to_download = [int(i) for i in args.album.split() if i.isdigit()] if args.album else []

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

        if not albums_to_download:
            print('Album list\n\nid\t\ttitle')
            print('-' * 80)
            for album in albums:
                print(u'{aid}\t{title}'.format(**album))

        for down_album in albums_to_download:
            valid = False
            for album in albums:
                if down_album == album['aid']:
                    valid = True
                    break
            if valid:
                print('Downloading {}'.format(down_album))
                if len(albums_to_download) > 1:
                    current_download_dir = get_download_dir(download_dir,
                                                            str(down_album))
                else:
                    current_download_dir = download_dir
                photos = request_api(
                    'photos.get',
                    params={'owner_id': '-{}'.format(gid),
                            'album_id': down_album}
                )
                photos_count = len(photos)
                pos_len = len(str(photos_count))
                for pos_raw, photo in enumerate(photos):
                    sys.stdout.write('\rDownloading {} of {}'.format(
                        pos_raw + 1, photos_count))
                    sys.stdout.flush()

                    src_keys = (
                        'src_xxxbig',
                        'src_xxbig',
                        'src_xbig',
                        'src_big',
                        'src',
                        'src_small',
                    )
                    photo_url = None
                    for key in src_keys:
                        if key in photo:
                            photo_url = photo[key]
                            break
                    if photo_url is None:
                        continue

                    response = requests.get(photo_url, stream=True)
                    ext = photo_url.split('.')[-1]
                    pos = str(pos_raw + 1).rjust(pos_len, '0')
                    with open('{}/{}.{}'.format(current_download_dir, pos, ext), 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                print('\n')
            else:
                print('Wrong album id {}'.format(down_album))
