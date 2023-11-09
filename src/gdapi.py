import requests
from typing import Optional


class GDAPIConf:
    REAUTH_URL = 'https://oauth2.googleapis.com/token'
    CLIENT_ID = '457607414709-7oc45nq59frd7rre6okq22fafftd55g1.apps.googleusercontent.com'
    __slots__ = ('refresh_token', 'access_token', 'id_token', 'scope')

    def __init__(self, refresh_token: str, access_token: Optional[str] = None, id_token: Optional[str] = None, scope: Optional[str] = None):
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.id_token = id_token
        self.scope = scope

    def refresh(self, session: Optional[requests.Session] = None, write: bool = False):
        up_headers = True
        data = {
            'refresh_token': self.refresh_token,
            'emm_support': 1,
            'device_os': 'iOS',
            'client_id': self.CLIENT_ID,
            'gpsdk': 'gid-5.0.2',
            'grant_type': 'refresh_token'
        }
        if session is None:
            up_headers = False
            session = requests.Session()
        response = session.post(self.REAUTH_URL, data=data)
        if response.status_code != 200:
            raise Exception(f"Could not refresh token! Status: {response.status_code}\nReason: {response.reason}")
        data = response.json()

        self.access_token = data['access_token']
        self.id_token = data['id_token']
        self.scope = data['scope']

        if up_headers:
            session.headers.update({"authorization": f"Bearer {self.access_token}"})
        if write:
            self.write_conf()

    def write_conf(self, filename: str = ".deltasync"):
        with open(filename, "w") as conf:
            conf.writelines([
                f"REFRESH_TOKEN={self.refresh_token}",
                f"ACCESS_TOKEN={self.access_token}",
                f"ID_TOKEN={self.id_token}",
                f"CLIENT_ID={self.CLIENT_ID}",
                f"SCOPE={self.scope}",
            ])

    @classmethod
    def from_conf(cls, filename: str = ".deltasync"):
        try:
            with open(filename, "r") as file:
                conf = {line.split("=")[0]: line.split("=")[1] for line in file.readlines() if line != ''}
                r = cls(conf['REFRESH_TOKEN'], getattr(conf, 'ACCESS_TOKEN', None), getattr(conf, 'ID_TOKEN', None))
        except FileNotFoundError:
            raise FileNotFoundError(f"File {filename} not found! Please provide a valid path to a configuration file")
        return r


class DeltaGDAPI:
    API_URL = 'https://www.googleapis.com/drive/v3/files'
    UPLOAD_URL = 'https://www.googleapis.com/upload/drive/v3/files'
    def __init__(self, conf: GDAPIConf):
        self.session = requests.Session()
        self._conf = conf
        if self._conf.access_token is None:
            self._conf.refresh(self.session, True)
        self._files = []

    def search_file(self, query: Optional[str] = None, fields: Optional[str] = None, page_size: int = 1000) -> list[dict]:
        "Searches files on Google Drive"
        if query is None:
            query = "'appDataFolder' in parents"
        else:
            query = f"'appDataFolder' in parents and {query}"

        if fields is None:
            fields = "nextPageToken, files(id, mimeType, name, headRevisionId, modifiedTime, appProperties, size)"

        # These parameters are how we get every file
        params = {
                'fields': fields,
                # fields is how we tell GDrive to return the data
                'q': query,
                # q is the actual query of the files, Google has their own query lang
                'pageSize': page_size,
                # The amount of items each page should return, 1000 almost guarantees we get every file
                'spaces': 'appDataFolder'
                # Make sure we stick to this space, otherwise we get invalid auth/etc
        }
        response = self.session.get(self.API_URL, params=params)
        if response.status_code > 400:
            print("Refreshing token..")
            self._conf.refresh()
            response = self.session.get(self.API_URL, params=params)

        return response.json()['files']

    def download_file(self, file_id: str) -> bytes:
        "Downloads the specified `file_id` from Google Drive, returns a bytes object representing the files' contents"
        return self.session.get(self.API_URL + f"/{file_id}", params={'alt':'media'}).content

    @property
    def files(self) -> list[dict]:
        '''List of files returned by the Google Drive API, will have a caching system'''
        # TODO: Actual file caching
        if len(self._files) == 0:
            self._files = [f for f in self.search_file()]
        return self._files


if __name__ == '__main__':
    dapi = DeltaGDAPI(GDAPIConf.from_conf())
    print(len(dapi.files))

