from lxml import html, etree
from enum import Enum, auto
import re


class TildesTopic:
    """Represents a single topic on Tildes, generated from the entire page.

    :ivar List[str] tags: List of tags this topic has.
    :ivar str title: The title of this topic.
    :ivar Optional[str] content_html: The text of this topic as rendered by the site.
    :ivar Optional[str] link: The link of this topic.
    :ivar str author: The topic author's username.
    :ivar str timestamp: The topic's creation timestamp.
    :ivar int num_votes: The amount of votes this topic has received.
    :ivar List[TildesComment] comments: Top level comments in this topic."""

    def __init__(self, text):
        self._tree = html.fromstring(text)

        self.tags = []
        for element in self._tree.cssselect("ul.topic-tags > li > a"):
            self.tags.append(element.text)

        self.title = self._tree.cssselect("article.topic-full > header > h1")[0].text
        try:
            self.content_html = str(
                etree.tostring(self._tree.cssselect("div.topic-full-text")[0])
            )
        except IndexError:
            self.content_html = None

        try:
            self.link = self._tree.cssselect("div.topic-full-link > a")[0].attrib[
                "href"
            ]
        except IndexError:
            self.link = None

        self.author = self._tree.cssselect("a.link-user")[0].text
        self.timestamp = self._tree.cssselect("time")[0].attrib["datetime"]
        try:
            self.num_votes = int(
                self._tree.cssselect("span.topic-voting-votes")[0].text
            )
        except IndexError:
            self.num_votes = 0

        comments = self._tree.cssselect("ol#comments > li > article")
        self.comments = []
        for comment in comments:
            self.comments.append(TildesComment(etree.tostring(comment)))


class TildesComment:
    """Represents a single comment on Tildes, generated from its surrounding ``<article>`` tag.

        :ivar str id36: The id36 of this comment.
        :ivar str content_html: This comment's content as rendered by the site.
        :ivar str author: The comment author's username.
        :ivar str timestamp: The comment's creation timestamp.
        :ivar int num_votes: The amount of votes this comment has received.
        :ivar List[TildesComment] children: Top level replies to this comment."""

    def __init__(self, text):
        self._tree = html.fromstring(text)
        self.id36 = self._tree.cssselect("article.comment")[0].attrib[
            "data-comment-id36"
        ]
        self.author = self._tree.cssselect("a.link-user")[0].text
        self.timestamp = self._tree.cssselect("time.comment-posted-time")[0].attrib[
            "datetime"
        ]
        self.content_html = str(
            etree.tostring(self._tree.cssselect("div.comment-text")[0])
        )
        vote_btn_text = "0"
        try:
            vote_btn_text = self._tree.cssselect(
                "button[name='vote'], div.comment-votes"
            )[0].text
            self.num_votes = int(re.findall("[0-9]+", vote_btn_text)[0])
        except IndexError:
            self.num_votes = 0

        self.children = []
        comments = self._tree.cssselect("ol.comment-tree-replies > li > article")
        for comment in comments:
            self.children.append(TildesComment(etree.tostring(comment)))


class TildesNotification:
    """Represents a single notification on Tildes, generated from its surrounding ``<li>`` tag.

    :ivar str subject: The id36 of the comment that triggered the notification.
    :ivar TildesNotificationKind kind: The kind of notification."""

    def __init__(self, text):
        self._tree = html.fromstring(text)
        self.subject = self._tree.cssselect("article.comment")[0].attrib[
            "data-comment-id36"
        ]
        notification_heading = self._tree.cssselect("h2.heading-notification")[0].text
        if "You were mentioned in a comment" in notification_heading:
            self.kind = TildesNotificationKind.MENTION
        elif "Reply to your topic" in notification_heading:
            self.kind = TildesNotificationKind.TOPIC_REPLY
        elif "Reply to your comment" in notification_heading:
            self.kind = TildesNotificationKind.COMMENT_REPLY
        else:
            self.kind = TildesNotificationKind.UNKNOWN


class TildesNotificationKind(Enum):
    """Enum representing the possible kinds of notification."""

    UNKNOWN = auto()
    MENTION = auto()
    TOPIC_REPLY = auto()
    COMMENT_REPLY = auto()


class TildesConversation:
    """Represents a conversation on Tildes, generated from the entire page.

    :ivar str title: The Subject of this conversation.
    :ivar List[TildesMessage] entries: The messages in this conversation in order."""

    def __init__(self, text):
        self._tree = html.fromstring(text)
        self.title = self._tree.cssselect("h1.heading-main")[0].text
        self.entries = []
        for entry in self._tree.cssselect("article.message"):
            self.entries.append(TildesMessage(etree.tostring(entry)))


class TildesMessage:
    """Represents a message in a conversation on Tildes, generated from its surrounding ``<article>`` tag.

    :ivar str author: The message author's username.
    :ivar str timestamp: The message's creation timestamp.
    :ivar str content_html: The message's content as rendered by the site."""

    def __init__(self, text):
        self._tree = html.fromstring(text)
        self.author = self._tree.cssselect("a.link-user")[0].text
        self.timestamp = self._tree.cssselect("time.time-responsive")[0].attrib[
            "datetime"
        ]
        self.content_html = str(
            etree.tostring(self._tree.cssselect("div.message-text")[0])
        )
