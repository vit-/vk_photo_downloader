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
    parser.add_argument('owner', help='Owner name or id')
    parser.add_argument('-u', help='Owner is user', action='store_true',
                        dest='source_is_user')
    parser.add_argument('-a', '--album', nargs='*', type=int,
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

    req_args, req_kwargs = ('groups.getById', ), {'params': {'group_id': args.owner}}
    if args.source_is_user:
        req_args, req_kwargs = ('users.get', ), {'params': {'user_ids': args.owner}}

    try:
        owner_info = request_api(*req_args, **req_kwargs)[0]
    except VKException:
        print('Can\'t find owner with name or id {}'.format(args.owner))
    else:
        if args.source_is_user:
            owner_id = owner_info['uid']
        else:
            owner_id = '-{}'.format(owner_info['gid'])

        albums = request_api('photos.getAlbums', params={'owner_id': owner_id})
        download_dir = get_download_dir(args.path)
        print('Saving to {}...'.format(download_dir))

        if not args.album:
            print('Album list\n\nid\t\ttitle')
            print('-' * 80)
            for album in albums:
                print(u'{aid}\t{title}'.format(**album))
            sys.exit(0)

        for down_album in args.album:
            valid = False
            for album in albums:
                if down_album == album['aid']:
                    valid = True
                    break
            if valid:
                print('Downloading {}'.format(down_album))
                if len(args.album) > 1:
                    current_download_dir = get_download_dir(download_dir,
                                                            str(down_album))
                else:
                    current_download_dir = download_dir
                photos = request_api(
                    'photos.get',
                    params={'owner_id': owner_id, 'album_id': down_album}
                )
                photos_count = len(photos)
                pos_len = len(str(photos_count))
                photo_suffixes = ['_xxxbig', '_xxbig', '_xbig',
                                  '_big', '_small', '']

                for pos_raw, photo in enumerate(photos):
                    sys.stdout.write('\rDownloading {} of {}'.format(
                        pos_raw + 1, photos_count))
                    sys.stdout.flush()
                    for suffix in photo_suffixes:
                        key = 'src{}'.format(suffix)
                        if key in photo:
                            photo_url = photo[key]
                            response = requests.get(photo_url, stream=True)
                            ext = photo_url.split('.')[-1]
                            pos = str(pos_raw + 1).rjust(pos_len, '0')
                            file_name = '{}/{}.{}'.format(download_dir,
                                                          pos, ext)
                            with open(file_name, 'wb') as f:
                                for chunk in response.iter_content(1024):
                                    f.write(chunk)
                            break
                print('\n')
            else:
                print('Wrong album id {}'.format(down_album))
