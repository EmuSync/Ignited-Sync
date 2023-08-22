import requests

s = requests.Session()

API_URL = 'https://www.googleapis.com/drive/v3/files'

# Access token we can intercept from Delta
access_token = "ya29.a0AfB_byBAa2hl6rljEzfyWktsCf_74Akxzt-7rz7FVR4HUeOPjNUOQVBXZBwEYYTomRu48Y4TDFct9I-wwHCuhnpXEQrvKj-LqOD51fOZ1fwRn9v2IUpkplRSxGg2lYqLURxadpD58waqz4Il0WWBhn5bB52dh-W5u8bxErTlaCgYKAckSARMSFQHsvYlspEr10vw-iu7rQojfk_0zZw0175"

# Might as well be a good internet samaritan
headers = {
        'authorization': f'Bearer {access_token}',
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
