import requests
import favicon


def get_icon_url(url):
    try:
        icons = favicon.get(url)
        icon = icons[0]
        return icon.url
    except requests.exceptions.ConnectionError as e:
        print('404')
        print(e)
    except IndexError as e:
        print('no icon')
        print(e)


def get_icon(url, local_file_name):
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
    except:
        print('error')


def download_image(url, local_file_path):
    try:
        response = requests.get(url, stream=True)
    except requests.exceptions.HTTPError as e:
        print('404')
        print(e)

    with open(local_file_path, 'wb') as image:
        for chunk in response.iter_content(1024):
            image.write(chunk)
