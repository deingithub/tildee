from lxml import html, etree
from enum import Enum, auto


class TildesTopic:
    """"Represents a single topic on Tildes."""

    def __init__(self, text):
        self._tree = html.fromstring(text)

        self.tags = []
        for element in self._tree.cssselect("ul.topic-tags > li > a"):
            self.tags.append(element.text)

        self.title = self._tree.cssselect("article.topic-full > header > h1")[0].text
        try:
            self.content_html = str(etree.tostring(
                self._tree.cssselect("div.topic-full-text")[0]
            ))
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

        comments = self._tree.cssselect("ol#comments > li > article")
        self.comments = []
        for comment in comments:
            self.comments.append(TildesComment(etree.tostring(comment)))


class TildesComment:
    """Represents a single comment on Tildes."""

    def __init__(self, text):
        self._tree = html.fromstring(text)
        self.id36 = self._tree.cssselect("article.comment")[0].attrib[
            "data-comment-id36"
        ]
        self.author = self._tree.cssselect("a.link-user")[0].text
        self.timestamp = self._tree.cssselect("time.comment-posted-time")[0].attrib[
            "datetime"
        ]
        self.content_html = str(etree.tostring(self._tree.cssselect("div.comment-text")[0]))
        self.children = []
        comments = self._tree.cssselect("ol.comment-tree-replies > li > article")
        for comment in comments:
            self.children.append(TildesComment(etree.tostring(comment)))


class TildesNotification:
    """Represents a single notification on Tildes."""

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
    UNKNOWN = auto()
    MENTION = auto()
    TOPIC_REPLY = auto()
    COMMENT_REPLY = auto()


class TildesConversation:
    """Represents a conversation on Tildes."""

    def __init__(self, text):
        self._tree = html.fromstring(text)
        self.title = self._tree.cssselect("h1.heading-main")[0].text
        self.entries = []
        for entry in self._tree.cssselect("article.message"):
            self.entries.append(TildesMessage(etree.tostring(entry)))


class TildesMessage:
    """Represents a message in a conversation on Tildes."""

    def __init__(self, text):
        self._tree = html.fromstring(text)
        self.author = self._tree.cssselect("a.link-user")[0].text
        self.timestamp = self._tree.cssselect("time.time-responsive")[0].attrib[
            "datetime"
        ]
        self.content_html = str(etree.tostring(self._tree.cssselect("div.message-text")[0]))
