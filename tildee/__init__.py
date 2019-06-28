__version__ = "0.1.0"

import requests
from lxml import html


class TildesClient:
    """A client for the Tildes API."""

    def __init__(
        self, username, password, base_url="https://tildes.net", verify_ssl=True
    ):
        """Logs in using username and password.

        Override base_url and if necessary verify_ssl to change the site Tildee uses."""
        self.username = username
        self.base_url = base_url
        self.__headers__ = {"Referer": base_url}
        self.__verify_ssl__ = verify_ssl
        self.__login__(password)

    def __login__(self, password):
        login_page = requests.get(self.base_url + "/login", verify=self.__verify_ssl__)
        self.__csrf_token__ = (
            html.fromstring(login_page.content)
            .cssselect("meta[name=csrftoken]")[0]
            .attrib["content"]
        )
        login_request = requests.post(
            self.base_url + "/login",
            data={
                "csrf_token": self.__csrf_token__,
                "username": self.username,
                "password": password,
            },
            cookies=login_page.cookies,
            headers=self.__headers__,
            verify=self.__verify_ssl__,
        )
        login_request.raise_for_status()
        self.__cookies__ = login_page.cookies

    def get(self, route):
        """Fetch a page using HTTP GET. Intended for internal use."""
        r = requests.get(
            self.base_url + route,
            cookies=self.__cookies__,
            headers=self.__headers__,
            verify=self.__verify_ssl__,
        )
        r.raise_for_status()
        return r

    def post(self, route, **kwargs):
        """Make a request using HTTP POST. Intended for internal use."""
        r = requests.post(
            self.base_url + route,
            cookies=self.__cookies__,
            headers=self.__headers__,
            data={"csrf_token": self.__csrf_token__, **kwargs},
            verify=self.__verify_ssl__,
        )
        r.raise_for_status()
        return r

    def ic_post(self, route, **kwargs):
        """Make a request using HTTP POST, adding an Intercooler header. Intended for internal use."""
        r = requests.post(
            self.base_url + route,
            cookies=self.__cookies__,
            headers={"x-ic-request": "true", **self.__headers__},
            data={"csrf_token": self.__csrf_token__, **kwargs},
            verify=self.__verify_ssl__,
        )
        r.raise_for_status()
        return r

    def create_topic(self, group, title, tags, **kwargs):
        """Post a topic into a group (without ~).
        Keyword arguments: `link` and/or `markdown`."""
        self.post(f"/~{group}/topics", title=title, tags=tags, **kwargs)

    def create_comment(self, parent_id36, markdown, top_level=True):
        """Post a comment."""
        if top_level:
            self.ic_post(f"/api/web/topics/{parent_id36}/comments", markdown=markdown)
        else:
            self.ic_post(f"/api/web/comments/{parent_id36}/replies", markdown=markdown)
