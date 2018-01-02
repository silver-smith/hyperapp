import os.path


LOCAL_REF_RESOLVER_URL_PATH = '~/.local/share/hyperapp/common/local_ref_resolver.url'
LOCAL_SERVER_REF_LIST_URL_PATH = '~/.local/share/hyperapp/common/local_server_ref_list.url'


def save_url_to_file(url_with_routes, path):
    url_path = os.path.expanduser(path)
    dir = os.path.dirname(url_path)
    if not os.path.isdir(dir):
        os.makedirs(dir)
    with open(url_path, 'w') as f:
        f.write(url_with_routes.to_str())
    return url_path
