import requests

# Access token we can intercept from Delta
# TODO: Figure out how to use refresh_token to automatically refresh access_token
with open(".env", "r") as file:
    conf = {line.split("=")[0]: line.split("=")[1] for line in file.read().split("\n") if line != ''}

s = requests.Session()

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
