# -*- coding: utf-8 -*-
import requests
#from six import BytesIO
try:
    from io import BytesIO as BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO 
    
#from StringIO import StringIO
import os
import sys

class Resp(BytesIO):
    def __init__(self, stream, status=200, headers=None):
        self.status = status
        self.headers = headers or {}
        self.reason = requests.status_codes._codes.get(
            status, ['']
        )[0].upper().replace('_', ' ')
        BytesIO.__init__(self, stream)

    @property
    def _original_response(self):
        return self

    @property
    def msg(self):
        return self

    def read(self, chunk_size, **kwargs):
        return BytesIO.read(self, chunk_size)

    def info(self):
        return self

    def get_all(self, name, default):
        result = self.headers.get(name)
        if not result:
            return default
        return [result]

    def getheaders(self, name):
        return self.get_all(name, [])

    def release_conn(self):
        self.close()
        
class LocalFileAdapter(requests.adapters.HTTPAdapter):
    def build_response_from_file(self, request):
        if sys.platform == 'win32':
            file_path = request.url[8:]
        else:
            file_path = request.url[7:]
        #file_path = request.url[7:]
        with open(file_path, 'rb') as file:
            buff = bytearray(os.path.getsize(file_path))
            file.readinto(buff)
            resp = Resp(buff)
            r = self.build_response(request, resp)
            return r

    def send(self, request, stream=False, timeout=None,
             verify=True, cert=None, proxies=None):
        return self.build_response_from_file(request)
    