import requests
import favicon
import os

def get_icon_url(url):
    try:
        icons = favicon.get(url)
        icon = icons[0]
        return icon.url
    except requests.exceptions.ConnectionError as e:
        print('404', e)
    except IndexError as e:
        print('no icon', e)
    except requests.exceptions.HTTPError as e:
        print('404', e)
    except requests.exceptions.MissingSchema as e:
        print('MissingSchema', e)
    except requests.exceptions.InvalidURL as e:
        print('InvalidURL', e)


def get_icon(url, local_file_name):
    print("get_icon")
    try:
        icons = favicon.get(url)
        icon = icons[0]
        download_image(url, f'{local_file_name}.{format(icon.format)}')
    except requests.exceptions.HTTPError as e:
        print('404')
        print(e)
    except requests.exceptions.ConnectionError as e:
        print('404')
        print(e)
    except requests.exceptions.MissingSchema as e:
        print('MissingSchema', e)
    except requests.exceptions.InvalidURL as e:
        print('InvalidURL', e)


def download_image(url, local_file_path):
    headers = {
        'User-Agent': 'brePodder/0.02'
    }

    try:
        response = requests.get(url, stream=True, headers=headers)
    except requests.exceptions.ConnectionError as e:
        print('404', e)
    except requests.exceptions.HTTPError as e:
        print('404')
        print(e)
    except requests.exceptions.MissingSchema as e:
        print('MissingSchema', e)
    except requests.exceptions.InvalidURL as e:
        print('InvalidURL', e)
    else:
        if response.status_code == 200:
            with open(local_file_path, 'wb') as image:
                for chunk in response.iter_content(1024):
                    image.write(chunk)
