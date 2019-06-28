__version__ = "0.1.0"

import requests
from lxml import html


class TildesClient:
    """A client for the (unstable) Tildes API."""

    def __init__(
        self, username, password, base_url="https://tildes.net", verify_ssl=True
    ):
        """Logs in using username and password.
        Override base_url and if necessary verify_ssl to change the site Tildee uses."""
        self.username = username
        self.base_url = base_url
        self._headers = {
            "Referer": base_url,
            "User-Agent": f"tildee.py Client [as {self.username}]",
        }
        self._verify_ssl = verify_ssl
        self._login(password)

    def __del__(self):
        self._logout()

    def _login(self, password):
        login_page = requests.get(
            self.base_url + "/login", headers=self._headers, verify=self._verify_ssl
        )
        self._csrf_token = (
            html.fromstring(login_page.content)
            .cssselect("meta[name=csrftoken]")[0]
            .attrib["content"]
        )
        login_request = requests.post(
            self.base_url + "/login",
            data={
                "csrf_token": self._csrf_token,
                "username": self.username,
                "password": password,
            },
            cookies=login_page.cookies,
            headers=self._headers,
            verify=self._verify_ssl,
        )
        login_request.raise_for_status()
        self._cookies = login_page.cookies

    def _logout(self):
        self._post("/logout")

    def _get(self, route):
        r = requests.get(
            self.base_url + route,
            cookies=self._cookies,
            headers=self._headers,
            verify=self._verify_ssl,
        )
        r.raise_for_status()
        return r

    def _post(self, route, **kwargs):
        r = requests.post(
            self.base_url + route,
            cookies=self._cookies,
            headers=self._headers,
            data={"csrf_token": self._csrf_token, **kwargs},
            verify=self._verify_ssl,
        )
        r.raise_for_status()
        return r

    def _ic_post(self, route, **kwargs):
        """Make a request using HTTP POST, adding an Intercooler header. Intended for internal use."""
        r = requests.post(
            self.base_url + route,
            cookies=self._cookies,
            headers={"x-ic-request": "true", **self._headers},
            data={"csrf_token": self._csrf_token, **kwargs},
            verify=self._verify_ssl,
        )
        r.raise_for_status()
        return r

    def create_topic(self, group, title, tags, **kwargs):
        """Post a topic into a group (without ~).
        Returns new topic's id36."""
        r = self._post(f"/~{group}/topics", title=title, tags=tags, **kwargs)
        return r.url.split("/")[-2]

    def create_comment(self, parent_id36, markdown, top_level=True):
        """Post a comment.
        Returns new comment's id36."""
        r = None
        if top_level:
            r = self._ic_post(
                f"/api/web/topics/{parent_id36}/comments", markdown=markdown
            )
        else:
            r = self._ic_post(
                f"/api/web/comments/{parent_id36}/replies", markdown=markdown
            )
        tree = html.fromstring(r.text)
        return tree.cssselect("article")[0].attrib["data-comment-id36"]

    def fetch_topic(self, topic_id36):
        """Returns a topic as an object for further processing"""
        r = self._get(f"/~group_name_here/{topic_id36}")
        return TildesTopic(r.text)


class TildesTopic:
    def __init__(self, text):
        self._tree = html.fromstring(text)

    def tags(self):
        tags = []
        for element in self._tree.cssselect("ul.topic-tags > li > a"):
            tags.append(element.text)
        return tags
