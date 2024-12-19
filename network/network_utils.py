import gzip
import ssl
import urllib.parse
import urllib.error
from urllib.request import Request
from typing import Union, Dict, Any, Tuple, List
import requests
import json
import urllib.request
from common.logger import logger

# 不使用代理处理request
no_proxy_handler = urllib.request.ProxyHandler({})
opener = urllib.request.build_opener(no_proxy_handler)

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def get_request(
    url: str,
    proxy_addr: Union[str, None] = None,
    headers: Union[dict, None] = None,
    data: Union[dict, bytes, None] = None,
    json_data: Union[dict, list, None] = None,
    timeout: int = 20,
    abroad: bool = False,
    content_conding: str = 'utf-8',
    redirect_url: bool = False,
) -> Union[str, Any]:
    if headers is None:
        headers = {}

    cookies = {}
    try:
        if proxy_addr:
            proxies = {
                'http': proxy_addr,
                'https': proxy_addr
            }
            if data or json_data:
                response = requests.post(
                    url,
                    data=data,
                    json=json_data,
                    headers=headers,
                    proxies=proxies,
                    timeout=timeout
                )
            else:
                response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)

            cookies = response.cookies.get_dict()
            if redirect_url:
                return response.url
            resp_str = response.text
        else:
            if data and not isinstance(data, bytes):
                data = urllib.parse.urlencode(data).encode(content_conding)
            if json_data and isinstance(json_data, (dict, list)):
                data = json.dumps(json_data).encode(content_conding)

            req = urllib.request.Request(url, data=data, headers=headers)

            try:
                if abroad:
                    response = urllib.request.urlopen(req, timeout=timeout)
                else:
                    response = opener.open(req, timeout=timeout)
                if redirect_url:
                    return response.url
                content_encoding = response.info().get('Content-Encoding')
                cookies = response.info().get_all("Set-Cookie", [])
                try:
                    if content_encoding == 'gzip':
                        with gzip.open(response, 'rt', encoding=content_conding) as gzipped:
                            resp_str = gzipped.read()
                    else:
                        resp_str = response.read().decode(content_conding)
                finally:
                    response.close()

            except urllib.error.HTTPError as e:
                if e.code == 400:
                    resp_str = e.read().decode(content_conding)
                else:
                    raise
            except urllib.error.URLError as e:
                logger.error("URL Error:", e)
                raise
            except Exception as e:
                logger.error("An error occurred:", e)
                raise

    except Exception as e:
        resp_str = str(e)

    return {"response": resp_str, "cookies": cookies}
