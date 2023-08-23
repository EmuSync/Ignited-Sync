import requests


class DeltaEmuSync:
    REAUTH_URL = 'https://oauth2.googleapis.com/token'
    API_URL = 'https://www.googleapis.com/drive/v3/files'
    CLIENT_ID = '457607414709-7oc45nq59frd7rre6okq22fafftd55g1.apps.googleusercontent.com'
    def __init__(self, conf: dict = None):
        self._files = []

        if conf is None:
            with open(".deltasync", "r") as file:
                conf = {line.split("=")[0]: line.split("=")[1] for line in file.read().split("\n") if line != ''}

        self.__refresh_tok = conf['REFRESH_TOKEN']
        try:
            self._client_id = conf['CLIENT_ID']
        except KeyError:
            self._client_id = self.CLIENT_ID
        try:
            self.__access_tok = conf['ACCESS_TOKEN']
            self.__id_tok = conf['ID_TOKEN']
            self._scope = conf['SCOPE']
        except KeyError:
            self.refresh_token()

        self.session = requests.Session()
        self.session.headers.update({'user-agent': 'emusync 0.0.0'})
        self.session.headers.update({"authorization": f"Bearer {self.__access_tok}"})

    def refresh_token(self) -> bool:
        data = {
            'refresh_token': self.__refresh_tok,
            'emm_support': 1,
            'device_os': 'iOS 17.0',
            'client_id': self._client_id,
            'gpsdk': 'gid-5.0.2',
            'grant_type': 'refresh_token'
         }
        refdata = self.session.post(self.REAUTH_URL, data=data).json()
        self.__access_tok = refdata['access_token']
        self.__id_tok = refdata['id_token']
        self._scope = refdata['scope']

        self.session.headers.update({"authorization": f"Bearer {self.__access_tok}"})
        with open(".deltasync", "w") as file:
            file.write(f"REFRESH_TOKEN={self.__refresh_tok}\n"
                       f"ACCESS_TOKEN={self.__access_tok}\n"
                       f"ID_TOKEN={self.__id_tok}\n"
                       f"CLIENT_ID={self._client_id}\n"
                       f"SCOPE={self._scope}\n")

        return True

    def search_file(self, query: str = None, fields: str = None, page_size: int = 1000) -> list[dict]:
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
            self.refresh_token()
            response = self.session.get(self.API_URL, params=params)
            if response.status_code > 250:
                raise EnvironmentError("Could not refresh token, response: {response.status_code}"
                                       " Reason: {response.reason}")
        return response.json()['files']

    def download_file(self, file_id: str) -> bytes:
        return self.session.get(self.API_URL + f"/{file_id}", params={'alt':'media'}).content

    @property
    def files(self) -> list[dict]:
        # TODO: Actual file caching
        if len(self._files) == 0:
            self._files = self.search_file()
        return self._files


if __name__ == '__main__':
    ds = DeltaEmuSync()
    print(ds.files)

