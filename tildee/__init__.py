__version__ = "0.2.3"

import requests
from requests import Response
from lxml import html, etree
from tildee.models import (
    TildesTopic,
    TildesComment,
    TildesNotification,
    TildesConversation,
    TildesPartialTopic,
)
from typing import Union, List, Optional


class TildesClient:
    """Initializes client and logs in.

    :param str username: The username to log in with.
    :param str password: The password to log in with.
    :param str base_url: The site to log in to.
    :param bool verify_ssl: Whether to check SSL certificate validity.
    """

    def __init__(
        self,
        username: str,
        password: str,
        base_url: str = "https://tildes.net",
        verify_ssl: bool = True,
    ):
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

    def _login(self, password: str):
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

    def _get(self, route: str) -> Response:
        r = requests.get(
            self.base_url + route,
            cookies=self._cookies,
            headers=self._headers,
            verify=self._verify_ssl,
        )
        r.raise_for_status()
        return r

    def _post(self, route: str, **kwargs) -> Response:
        r = requests.post(
            self.base_url + route,
            cookies=self._cookies,
            headers=self._headers,
            data={"csrf_token": self._csrf_token, **kwargs},
            verify=self._verify_ssl,
        )
        r.raise_for_status()
        return r

    def _ic_req(
        self,
        route: str,
        method: Optional[str] = None,
        ic_trigger: Optional[str] = None,
        **kwargs,
    ) -> Response:
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

    def _ic_get(self, route: str, **kwargs) -> Response:
        r = requests.get(
            self.base_url + route,
            cookies=self._cookies,
            headers={"x-ic-request": "true", **self._headers},
            data={"csrf_token": self._csrf_token, **kwargs},
            verify=self._verify_ssl,
        )
        r.raise_for_status()
        return r

    def create_topic(
        self, group: str, title: str, tags: Union[str, List[str]], **kwargs
    ) -> str:
        """Post a topic into a group, returns new topic's id36. Either a link or markdown must be passed.

        :param str group: The group to post in, without a ~ in front.
        :param str title: The topic's title.
        :type tags: str or List[str]
        :param tags: Comma separated string or list of tags.
        :kwarg str markdown: The topic's content as markdown.
        :kwarg str link: The topic's link.
        :rtype: str
        :return: New topic's id36.
        """
        if isinstance(tags, list):
            # Stringify list and remove braces
            tags = str(tags)[1:-1].replace("'", "")
        r = self._post(f"/~{group}/topics", title=title, tags=tags, **kwargs)
        return r.url.split("/")[-2]

    def create_comment(
        self, parent_id36: str, markdown: str, top_level: bool = True
    ) -> str:
        """Post a comment, returns new comment's id36.

        :param str markdown: The comment's content as markdown.
        :param str parent_id36: The parent entity's id36. Can be a topic or comment.
        :param bool top_level: Set this to False if the comment's a reply to another comment.
        :rtype: str
        :return: The new comment's id36."""
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

    def fetch_topic(self, topic_id36: str) -> TildesTopic:
        """Fetches, parses and returns a topic as an object for further processing.

        :param str topic_id36: The id36 of the topic to fetch.
        :rtype: TildesTopic
        :return: The requested topic."""
        r = self._get(f"/~group_name_here/{topic_id36}")
        return TildesTopic(r.text)

    def fetch_topic_listing(self, path: str) -> List[TildesPartialTopic]:
        """Fetches, parses and returns all topics from a certain URL.

        I.e. an empty string for the home page, ``~group`` for a group or ``search?q=a`` for a search.
        Appends ``per_page=100`` to the path for maximum results.

        :param str path: The URL to fetch from.
        :rtype: List[TildesPartialTopic]
        :return: The requested topics."""
        r = None
        if "?" in path:
            r = self._get(f"/{path}&per_page=100")
        else:
            r = self._get(f"/{path}?per_page=100")

        articles = html.fromstring(r.text).cssselect("article.topic")
        topics = []
        for article in articles:
            topics.append(TildesPartialTopic(etree.tostring(article)))

        return topics

    def fetch_filtered_topic_listing(self, group: str = "", tag: str = "", **kwargs):
        """Fetches a filtered list of topics. Automatically adds ``per_page=100`` to the query string.

        :param str group: The group to filter for. Leave empty to search all subscribed groups.
        :param str tag: The tag to filter for, Tildes currently only supports filtering for one tag.
        :rtype: List[TildesPartialTopic]
        :return: Up to 100 topics matching the filters."""
        query_str: str = ""
        if group:
            query_str += f"~{group}/"
        if tag:
            query_str += f"?tag={tag.replace(' ', '_')}"
        if kwargs:
            if tag:
                query_str += "&"
            else:
                query_str += "?"

            for k, v in kwargs.items():
                query_str += f"{k}={v}&"

            query_str = query_str[:-1]

        return self.fetch_topic_listing(query_str)

    def fetch_search_topic_listing(self, query: str = "", **kwargs):
        """Fetches a search result's list of topics. Automatically adds ``per_page=100`` to the query string.

        :param str query: The string to search for.
        :rtype: List[TildesPartialTopic]
        :return: Up to 100 topics matching the query string."""
        if not query:
            raise RuntimeError("Query string must not be empty.")
        query_str: str = f"search?q={query}"
        if kwargs:
            query_str += "&"

            for k, v in kwargs.items():
                query_str += f"{k}={v}&"

            query_str = query_str[:-1]

        return self.fetch_topic_listing(query_str)

    def fetch_comment(self, comment_id36: str) -> TildesComment:
        """Fetches, parses and returns a single comment as an object for further processing.

        This endpoint doesn't include a comments' children.

        :param str comment_id36: The id36 of the comment to fetch.
        :rtype: TildesComment
        :return: The requested comment."""
        r = self._ic_get(f"/api/web/comments/{comment_id36}")
        fake_article = f'<article class="comment" data-comment-id36="{comment_id36}">{r.text}</article>'
        return TildesComment(fake_article)

    def edit_topic(self, topic_id36: str, **kwargs):
        """Interact with a topic in nearly any way possible; permission limits still apply, obviously.

        :param str topic_id36: The id36 of the topic to act on.
        :type tags: str or List[str]
        :kwarg tags: Comma separated string or list of tags.
        :kwarg str group: The new group for the topic, without ~ in front.
        :kwarg str title: The new title for the topic.
        :kwarg str link: The new link for the topic.
        :kwarg str content: The new markdown for the topic. Account must be topic author.
        :kwarg bool vote: Boolean, vote/unvote this topic.
        :kwarg bool bookmark: Boolean, bookmark/unbookmark this topic."""
        if "tags" in kwargs:
            if isinstance(kwargs["tags"], list):
                # Stringify list and remove braces
                kwargs["tags"] = str(kwargs["tags"])[1:-1].replace("'", "")
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

    def delete_topic(self, topic_id36: str):
        """Delete a topic. Account must be topic author.

        :param str topic_id36: The id36 of the topic to delete."""
        self._ic_req(f"/api/web/topics/{topic_id36}", "DELETE")

    def moderate_topic(self, topic_id36: str, **kwargs):
        """Moderate a topic, setting its locked/removed status. Account must be admin.

        :param str topic_id36: The id36 of the topic to act on.
        :kwarg bool lock: Boolean, lock/unlock comments.
        :kwarg bool remove: Boolean, remove/unremove this topic."""
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

    def edit_comment(self, comment_id36: str, **kwargs):
        """Interact with a comment in nearly any way possible; permission limits still apply, obviously.

        :param str comment_id36: The id36 of the comment to act on.

        :kwarg str content: The new markdown for the comment. Account must be comment author.
        :kwarg bool vote: Boolean, vote/unvote this comment.
        :kwarg bool bookmark: Boolean, bookmark/unbookmark this comment.
        """
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

    def delete_comment(self, comment_id36: str):
        """Delete a comment. Account must be comment author.

        :param str comment_id36: The id36 of the comment to delete."""
        self._ic_req(f"/api/web/comments/{comment_id36}", "DELETE")

    def moderate_comment(self, comment_id36: str, **kwargs):
        """Moderate a comment, setting its removed status. Account must be admin.

        :param str comment_id36: The id36 of the comment to act on.
        :kwarg bool remove: Boolean, remove/unremove comment."""
        if "remove" in kwargs:
            if kwargs["remove"]:
                self._ic_req(f"/api/web/comments/{comment_id36}/remove", "PUT")
            else:
                self._ic_req(f"/api/web/comments/{comment_id36}/remove", "DELETE")

    def fetch_unread_notifications(self) -> List[TildesNotification]:
        """Fetches, parses and returns a list of unread notifications as objects for further processing.

        :rtype: List[TildesNotification]
        :return: The list of unread notifications."""
        r = self._get(f"/notifications/unread")
        tree = html.fromstring(r.text)
        notifications = tree.cssselect("ol.post-listing-notifications > li")
        output = []
        for notification in notifications:
            output.append(TildesNotification(etree.tostring(notification)))
        return output

    def mark_notification_as_read(self, subject_id36: str):
        """Marks a notification as read.

        :param str subject_id36: The notification subject's id36 to mark."""
        self._ic_req(f"/api/web/comments/{subject_id36}/mark_read", "PUT")

    def fetch_unread_message_ids(self) -> List[str]:
        """Fetches IDs of unread messages.

        :rtype: List[str]
        :return: The list of unread conversations' id36s."""
        r = self._get("/messages/unread")
        tree = html.fromstring(r.text)
        new_messages = []
        for message_entry in tree.cssselect(
            "tr.message-list-unread > td.message-list-subject > a"
        ):
            new_messages.append(message_entry.attrib["href"].split("/")[-1])
        return new_messages

    def fetch_conversation(self, convo_id36: str) -> TildesConversation:
        """Fetches, parses and returns a conversation as TildesConversation object for further processing.

        :param str convo_id36: The target conversation's id36.
        :rtype: TildesConversation
        :return: The requested conversation."""
        r = self._get(f"/messages/conversations/{convo_id36}")
        return TildesConversation(r.text)

    def create_message(self, convo_id36: str, markdown: str):
        """Creates a message in an existing conversation.

        :param str convo_id36: The target conversation's id36.
        :param str markdown: The message's content as markdown."""
        self._ic_req(
            f"/api/web/messages/conversations/{convo_id36}/replies", markdown=markdown
        )

    def create_conversation(self, username: str, subject: str, markdown: str):
        """Creates a new conversation with a user.

        :param str username: The username of the recipient.
        :param str subject: The conversation's subject.
        :param str markdown: The first message's content as markdown."""
        self._ic_req(f"/user/{username}/messages", subject=subject, markdown=markdown)
