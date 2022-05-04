import requests
import favicon


def get_icon_url(url):
    icons = favicon.get(url)
    icon = icons[0]
    return icon.url


def get_icon(url, local_file_name):
    icons = favicon.get(url)
    icon = icons[0]
    download_image(url, f'{local_file_name}.{format(icon.format)}')


def download_image(url, local_file_path):
    response = requests.get(url, stream=True)
    with open(local_file_path, 'wb') as image:
        for chunk in response.iter_content(1024):
            image.write(chunk)
