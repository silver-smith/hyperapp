import os.path


LOCAL_REF_RESOLVER_URL_PATH = '~/.local/share/hyperapp/common/local_ref_resolver.url'
LOCAL_SERVER_REF_LIST_REF_PATH = '~/.local/share/hyperapp/common/local_server_ref_list.ref'


def save_data_to_file(data, path):
    full_path = os.path.expanduser(path)
    dir = os.path.dirname(full_path)
    if not os.path.isdir(dir):
        os.makedirs(dir)
    with open(full_path, 'wb') as f:
        f.write(data)
    return full_path

def save_url_to_file(url_with_routes, path):
    return save_data_to_file(url_with_routes.to_str().encode(), path)
