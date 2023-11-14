import arrow, requests, datetime, os
from arrow import Arrow
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Properties:
    sha1hash: str
    relationship_id: Optional[str] = None
    author: Optional[str] = None
    localized_name: Optional[str] = None
    game_name: Optional[str] = None
    game_id: Optional[str] = None
    object_id: Optional[str] = None
    object_type: Optional[str] = None
    previous_date: Optional[Arrow] = None
    previous_id: Optional[str] = None
    core_id: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict):
        return cls(
                data['harmony_sha1Hash'],
                data.get('harmony_relationshipIdentifier', None),
                data.get('harmony_author', None),
                data.get('harmony_localizedName', None),
                data.get('gameName', None),
                data.get('gameID', None),
                data.get('harmony_recordedObjectIdentifier', None),
                data.get('harmony_recordedObjectType', None),
                data.get('harmony_previousVersionDate', None),
                data.get('harmony_previousVersionIdentifier', None),
                data.get('coreID', None)
               )


@dataclass
class GFile:
    id: str
    name: str
    size: int
    modified: Arrow
    mime: str
    head_rev_id: str
    properties: Properties
    api: Optional['GDAPI'] = field(repr=False, default=None)

    @classmethod
    def from_api(cls, data: dict, api: Optional['GDAPI'] = None):
        return cls(
                data['id'],
                data['name'],
                int(data['size']),
                arrow.get(data['modifiedTime']),
                data['mimeType'],
                data['headRevisionId'],
                Properties.from_api(data['appProperties']),
                api
               )

    def download(self, session: Optional['GDAPI'] = None) -> bytes:
        "Download this files' bytes"
        if self.api is None:
            if session is None:
                raise Exception("Need an API session to download this file!")
            return session.download_file(self.id)
        return self.api.download_file(self.id)

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


class GDAPI:
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
    def files(self) -> list[GFile]:
        '''List of files returned by the Google Drive API, will have a caching system'''
        # TODO: Actual file caching
        if len(self._files) == 0:
            self._files = [GFile.from_api(f, self) for f in self.search_file()]
        return self._files
    
    def searchJsonFile(self, data, searchforid: str, inputValue: str):
        for i in data:
                if i['id'] == searchforid:
                    #print(i[inputValue])
                    return i[inputValue]

    def downloadRequestedFile(self, id, filePath):
        print(self) # get past argument error even if self is gone
        
        fileNameFromJson = dapi.searchJsonFile(dapi.files, id, "mimeType").replace("/",".")
        print("getting Details for ",fileNameFromJson)
        fullPath = filePath + "/" + fileNameFromJson
        fileModTime = dapi.searchJsonFile(dapi.files, id, "modifiedTime")
        #properties = ds.searchJsonFile(ds.files, id, "appProperties")
                
        convertToUnixTime = datetime.datetime.strptime(fileModTime.replace("T"," ").replace("Z",""),"%Y-%m-%d %H:%M:%S.%f").timestamp()
        print("Downloaded Modified TimeStamp:", convertToUnixTime)
        print("Downloading File: ",fileNameFromJson)

        # TODO: Add sha1hash verification
        DWfile = dapi.download_file(id)

        
        print("finished: ", fileNameFromJson)

        with open(fullPath, 'wb') as file:
            file.write(DWfile)
            os.utime(fullPath,(convertToUnixTime,convertToUnixTime))
            print("File Written to: ", fullPath)


if __name__ == '__main__':
    dapi = GDAPI(GDAPIConf.from_conf())
    print(len(dapi.files))
    print(type(dapi.files))
    print(dapi.files[1])

    # Downloads file via id and tells were to download
    dapi.downloadRequestedFile("1SsYTjZbvetM3ZB8QNz84HO5S48iLcWDgd_ONaldId2b4jRlrfg", "/run/media/deck/5b860f23-1efd-4ba5-8336-603c1dde8b94/git/Delta-Reversing/sync")

