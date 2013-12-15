import requests
from os import path

API_URL = 'https://api.vk.com/method'
PATH = path.dirname(path.abspath(__file__))

class VKException(Exception):
    pass

def request_api(method, params={}):
    response = requests.get('{}/{}'.format(API_URL, method), params=params)
    data = response.json()
    if 'error' in data:
        raise VKException('Code - {error_code}. Message - {error_msg}'.format(**data['error']))
    return data['response']

def create_parser():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('group', help='Owner name or id')
    parser.add_argument('-a', '--album', type=int, help='Specify album id to download')
    return parser

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()

    try:
        group_info = request_api('groups.getById', params={'group_id': args.group})[0]
    except VKException:
        print('Can\'t find group with name {}'.format(args.group))
    else:
        gid = group_info['gid']
        albums = request_api('photos.getAlbums', {'owner_id': '-{}'.format(gid)})
        if args.album:
            valid = False
            for album in albums:
                if args.album == album['aid']:
                    valid = True
                    break
            if valid:
                photos = request_api(
                    'photos.get', params={'owner_id': '-{}'.format(gid), 'album_id': args.album})
                pos_len = len(str(len(photos)))
                for pos_raw, photo in enumerate(photos):
                    try:
                        photo_url = photo['src_xxbig']
                    except KeyError:
                        continue
                    else:
                        response = requests.get(photo['src_xxbig'], stream=True)
                        ext = photo_url.split('.')[-1]
                        pos = str(pos_raw + 1).rjust(pos_len, '0')
                        with open('{}/{}.{}'.format(PATH, pos, ext), 'wb') as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
            else:
                print('Wrong album id')
        else:
            print('Album list (title/id)')
            print('-' * 80)
            for album in albums:
                print(u'{title} - {aid}'.format(**album))
