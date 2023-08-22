import requests

# Access token we can intercept from Delta
def read_conf():
    with open(".env", "r") as file:
        return {line.split("=")[0]: line.split("=")[1] for line in file.read().split("\n") if line != ''}

def write_conf(conf):
    with open(".env", "w") as file:
        for i, v in conf.items():
            file.write(f"{i}={v}\n")

conf = read_conf()

s = requests.Session()

def refresh_token(conf):
    data = {
        'refresh_token': conf['REFRESH_TOKEN'],
        'emm_support': 1,
        'device_os': 'iOS 17.0',
        'client_id': conf['CLIENT_ID'],
        'gpsdk': 'gid-5.0.2',
        'grant_type': 'refresh_token'
     }
    refdata = s.post('https://oauth2.googleapis.com/token', data=data).json()
    conf['ACCESS_TOKEN'] = refdata['access_token']
    conf['ID_TOKEN'] = refdata['id_token']
    conf['TYPE'] = refdata['token_type']
    conf['SCOPE'] = refdata['scope']
    write_conf(conf)
    return conf

API_URL = 'https://www.googleapis.com/drive/v3/files'

# Might as well be a good internet samaritan
headers = {
        'authorization': f'Bearer {conf["ACCESS_TOKEN"]}',
        'user-agent': 'emusync 0.0.0',
}
s.headers.update(headers)

# These parameters are how we get every file
params = {
        'fields': "nextPageToken, files(id, mimeType, name, headRevisionId, modifiedTime, appProperties, size)",
        # fields is how we tell GDrive to return the data
        'q': "'appDataFolder' in parents",
        # q is the actual query of the files, Google has their own query lang
        'pageSize': 1000,
        # The amount of items each page should return, 1000 almost guarantees we get every file
        'spaces': 'appDataFolder'
        # Make sure we stick to this space, otherwise we get invalid auth/etc
}

# Actual request to retrieve the list of files
response = s.get(API_URL, params=params)

def download_file(file_id):
    return s.get(f"{API_URL}/{file_id}?alt=media")
