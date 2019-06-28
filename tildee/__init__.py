__version__ = "0.1.0"

import requests
from lxml import html, etree
from tildee.models import (
    TildesTopic,
    TildesComment,
    TildesNotification,
    TildesConversation,
)


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

    def _ic_req(self, route, method=None, ic_trigger=None, **kwargs):
        r = requests.post(
            self.base_url + route,
            cookies=self._cookies,
            headers={
                "x-ic-request": "true",
                "X-HTTP-Method-Override": method,
                **self._headers,
            },
            data={
                "csrf_token": self._csrf_token,
                "ic-trigger-name": ic_trigger,
                **kwargs,
            },
            verify=self._verify_ssl,
        )
        r.raise_for_status()
        return r

    def _ic_get(self, route, **kwargs):
        r = requests.get(
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
            r = self._ic_req(
                f"/api/web/topics/{parent_id36}/comments", markdown=markdown
            )
        else:
            r = self._ic_req(
                f"/api/web/comments/{parent_id36}/replies", markdown=markdown
            )
        tree = html.fromstring(r.text)
        return tree.cssselect("article")[0].attrib["data-comment-id36"]

    def fetch_topic(self, topic_id36):
        """Fetches, parses and returns a topic as a TildesTopic object for further processing."""
        r = self._get(f"/~group_name_here/{topic_id36}")
        return TildesTopic(r.text)

    def fetch_comment(self, comment_id36):
        """Fetches, parses and returns a comment as a TildesComment object for further processing.
        This endpoint doesn't include children comments."""
        r = self._ic_get(f"/api/web/comments/{comment_id36}")
        fake_article = f'<article class="comment" data-comment-id36="{comment_id36}">{r.text}</article>'
        return TildesComment(fake_article)

    def edit_topic(self, topic_id36, **kwargs):
        """Interact with a topic in nearly any way possible.
        Allows editing tags, group, title, link and content as well as setting and removing bookmarks/votes.
        Server permission limits still apply, obviously."""
        if "tags" in kwargs:
            self._ic_req(
                f"/api/web/topics/{topic_id36}/tags", "PUT", tags=kwargs["tags"]
            )
        if "group" in kwargs:
            self._ic_req(
                f"/api/web/topics/{topic_id36}",
                "PATCH",
                "topic-move",
                group_path=kwargs["group"],
            )
        if "title" in kwargs:
            self._ic_req(
                f"/api/web/topics/{topic_id36}",
                "PATCH",
                "topic-title-edit",
                title=kwargs["title"],
            )
        if "link" in kwargs:
            self._ic_req(
                f"/api/web/topics/{topic_id36}",
                "PATCH",
                "topic-link-edit",
                link=kwargs["link"],
            )
        if "content" in kwargs:
            self._ic_req(
                f"/api/web/topics/{topic_id36}", "PATCH", markdown=kwargs["content"]
            )
        if "vote" in kwargs:
            if kwargs["vote"]:
                self._ic_req(f"/api/web/topics/{topic_id36}/vote", "PUT", "vote")
            else:
                self._ic_req(f"/api/web/topics/{topic_id36}/vote", "DELETE", "vote")
        if "bookmark" in kwargs:
            if kwargs["bookmark"]:
                self._ic_req(f"/api/web/topics/{topic_id36}/bookmark", "PUT")
            else:
                self._ic_req(f"/api/web/topics/{topic_id36}/bookmark", "DELETE")

    def moderate_topic(self, topic_id36, **kwargs):
        """Moderate a topic, setting its locked/removed status."""
        if "lock" in kwargs:
            if kwargs["lock"]:
                self._ic_req(f"/api/web/topics/{topic_id36}/lock", "PUT")
            else:
                self._ic_req(f"/api/web/topics/{topic_id36}/lock", "DELETE")
        if "remove" in kwargs:
            if kwargs["remove"]:
                self._ic_req(f"/api/web/topics/{topic_id36}/remove", "PUT")
            else:
                self._ic_req(f"/api/web/topics/{topic_id36}/remove", "DELETE")

    def edit_comment(self, comment_id36, **kwargs):
        """Interact with a comment in nearly any way possible.
        Allows editing content as well as setting and removing bookmarks/votes.
        Server permission limits still apply, obviously."""
        if "content" in kwargs:
            self._ic_req(
                f"/api/web/comments/{comment_id36}", "PATCH", markdown=kwargs["content"]
            )
        if "vote" in kwargs:
            if kwargs["vote"]:
                self._ic_req(f"/api/web/comments/{comment_id36}/vote", "PUT", "vote")
            else:
                self._ic_req(f"/api/web/comments/{comment_id36}/vote", "DELETE", "vote")
        if "bookmark" in kwargs:
            if kwargs["bookmark"]:
                self._ic_req(f"/api/web/comments/{comment_id36}/bookmark", "PUT")
            else:
                self._ic_req(f"/api/web/comments/{comment_id36}/bookmark", "DELETE")

    def moderate_comment(self, comment_id36, **kwargs):
        """Moderate a comment, setting its removed status."""
        if "remove" in kwargs:
            if kwargs["remove"]:
                self._ic_req(f"/api/web/comments/{comment_id36}/remove", "PUT")
            else:
                self._ic_req(f"/api/web/comments/{comment_id36}/remove", "DELETE")

    def fetch_unread_notifications(self):
        """Fetches, parses and returns a list of unread notifications as TildesNotification objects for further processing."""
        r = self._get(f"/notifications/unread")
        tree = html.fromstring(r.text)
        notifications = tree.cssselect("ol.post-listing-notifications > li")
        output = []
        for notification in notifications:
            output.append(TildesNotification(etree.tostring(notification)))
        return output

    def mark_notification_as_read(self, subject_id36):
        self._ic_req(f"/api/web/comments/{subject_id36}/mark_read", "PUT")

    def fetch_unread_message_ids(self):
        """Fetches IDs of unread messages."""
        r = self._get("/messages/unread")
        tree = html.fromstring(r.text)
        new_messages = []
        for message_entry in tree.cssselect(
            "tr.message-list-unread > td.message-list-subject > a"
        ):
            new_messages.append(message_entry.attrib["href"].split("/")[-1])
        return new_messages

    def fetch_conversation(self, convo_id36):
        """Fetches, parses and returns a conversation as TildesConversation object for further processing."""
        r = self._get(f"/messages/conversations/{convo_id36}")
        return TildesConversation(r.text)

    def create_message(self, convo_id36, markdown):
        """Creates a message in an existing conversation."""
        self._ic_req(
            f"/api/web/messages/conversations/{convo_id36}/replies", markdown=markdown
        )

    def create_conversation(self, username, subject, markdown):
        """Creates a new conversation with a user."""
        self._ic_req(f"/user/{username}/messages", subject=subject, markdown=markdown)
