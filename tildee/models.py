from lxml import html, etree
from enum import Enum, auto
import re


class TildesTopic:
    """Represents a single topic on Tildes, generated from the entire page.

    :ivar List[str] tags: List of tags this topic has.
    :ivar str group: The group this topic was posted in.
    :ivar str title: The title of this topic.
    :ivar TildesAccessStatus status: Status of this comment. If ``DELETED`` or ``REMOVED``, ``content_html``, ``link``, ``author``, ``timestamp``, ``comments``, ``log``, ``num_votes`` and ``num_comments`` are unavailable.
    :ivar Optional[str] content_html: The text of this topic as rendered by the site.
    :ivar Optional[str] link: The link of this topic.
    :ivar str author: The topic author's username.
    :ivar str timestamp: The topic's creation timestamp.
    :ivar int num_votes: The amount of votes this topic has received.
    :ivar int num_comments: The amount of comments on this topic.
    :ivar List[TildesTopicLogEntry] log: The associated topic log in chronological order.
    :ivar List[TildesComment] comments: Top level comments in this topic."""

    def __init__(self, text):
        self._tree = html.fromstring(text)

        self.group = self._tree.cssselect("a.site-header-context")[0].text[1:]

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

        if self._tree.cssselect("article.topic-full > .text-error"):
            error = self._tree.cssselect("article.topic-full > .text-error")[0]
            if "removed by site admin" in error.text:
                self.status = TildesAccessStatus.REMOVED
                self.author, self.timestamp = "", ""
                self.comments, self.log = [], []
                self.num_votes, self.num_comments = 0, 0
                return
            elif "deleted by author" in error.text:
                self.status = TildesAccessStatus.DELETED
                self.author, self.timestamp = "", ""
                self.comments, self.log = [], []
                self.num_votes, self.num_comments = 0, 0
                return
            else:
                raise (
                    RuntimeError(f'Unknown topic ({self.id36}) status: "{error.text}"')
                )

        self.author = self._tree.cssselect("a.link-user")[0].text
        self.timestamp = self._tree.cssselect("time")[0].attrib["datetime"]
        try:
            self.num_votes = int(
                self._tree.cssselect("span.topic-voting-votes")[0].text
            )
        except IndexError:
            self.num_votes = 0

        self.num_comments = self._tree.cssselect("header.topic-comments-header > h2")[
            0
        ].text.split(" ")[0]

        log_entries = self._tree.cssselect("ol.topic-log-listing > li")
        self.log = []
        for log_entry in log_entries:
            self.log.append(TildesTopicLogEntry(etree.tostring(log_entry)))
        self.log.reverse()

        comments = self._tree.cssselect("ol#comments > li > article")
        self.comments = []
        for comment in comments:
            self.comments.append(TildesComment(etree.tostring(comment)))


class TildesPartialTopic:
    """Represents a topic on Tildes as fetched from the topic listings, generated from its surrounding ``<article>`` tag. Has only reduced information available.

    :ivar str id36: The topic's id36.
    :ivar str title: The topic's title.
    :ivar Optional[str] group: The topic's group, if provided in the listing.
    :ivar str author: The topic's author.
    :ivar Optional[str] link: The topic's link, if available.
    :ivar Optional[str] content_html: The text of this topic as rendered by the site, if available.
    :ivar int num_votes: The amount of votes this topic has received.
    :ivar int num_comments: The amount of comments on this topic.
    :ivar List[str] tags: The tags on this topics.
    :ivar str timestamp: The topic's timestamp."""

    def __init__(self, text):
        self._tree = html.fromstring(text)
        self.id36 = self._tree.cssselect("article")[0].attrib["id"].split("-")[1]
        self.title = self._tree.cssselect("h1.topic-title > a")[0].text
        self.group = None
        try:
            self.group = self._tree.cssselect(".topic-group > a")[0].text[1:]
        except IndexError:
            pass

        self.author = self._tree.cssselect("article")[0].attrib["data-topic-posted-by"]
        self.link = None
        self.content_html = None
        if not self._tree.cssselect("header h1 > a")[0].attrib["href"].startswith("/"):
            self.link = self._tree.cssselect("header h1 > a")[0].attrib["href"]
        elif self._tree.cssselect(".topic-text-excerpt"):
            tree = self._tree.cssselect(".topic-text-excerpt")[0]
            etree.strip_elements(tree, "summary")
            self.content_html = str(etree.tostring(tree))
        try:
            self.num_votes = int(
                self._tree.cssselect("span.topic-voting-votes")[0].text
            )
        except IndexError:
            self.num_votes = 0
        self.num_comments = int(
            re.findall(
                "[0-9]+", self._tree.cssselect(".topic-info-comments > a")[0].text
            )[0]
        )

        self.tags = []
        for element in self._tree.cssselect("ul.topic-tags > li > a"):
            self.tags.append(element.text)

        self.timestamp = self._tree.cssselect("time")[0].attrib["datetime"]


class TildesComment:
    """Represents a single comment on Tildes, generated from its surrounding ``<article>`` tag.

        :ivar str id36: The id36 of this comment.
        :ivar TildesAccessStatus status: Status of this comment. If ``DELETED`` or ``REMOVED``, no data beyond ``id36`` are available.
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

        self.children = []
        comments = self._tree.cssselect("ol.comment-tree-replies > li > article")
        for comment in comments:
            self.children.append(TildesComment(etree.tostring(comment)))

        self.status = TildesAccessStatus.FULL
        if self._tree.cssselect("div.is-comment-removed"):
            self.status = TildesAccessStatus.REMOVED
            self.author, self.timestamp, self.content_html = "", "", ""
            self.num_votes = 0
            return
        elif self._tree.cssselect("div.is-comment-deleted"):
            self.status = TildesAccessStatus.DELETED
            self.author, self.timestamp, self.content_html = "", "", ""
            self.num_votes = 0
            return
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
        if notification_heading.startswith("You were mentioned in a comment"):
            self.kind = TildesNotificationKind.MENTION
        elif notification_heading.startswith("Reply to your topic"):
            self.kind = TildesNotificationKind.TOPIC_REPLY
        elif notification_heading.startswith("Reply to your comment"):
            self.kind = TildesNotificationKind.COMMENT_REPLY
        else:
            self.kind = TildesNotificationKind.UNKNOWN


class TildesNotificationKind(Enum):
    """Enum representing the possible kinds of notification."""

    UNKNOWN = auto()
    MENTION = auto()
    TOPIC_REPLY = auto()
    COMMENT_REPLY = auto()


class TildesAccessStatus(Enum):
    """Enum representing the possible visibility statuses of comments or topics."""

    #: Full content is available.
    FULL = auto()
    #: Comment/Topic removed by site admin, only reduced data available.
    REMOVED = auto()
    #: Comment/Topic deleted by its author, only reduced data available.
    DELETED = auto()


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


class TildesTopicLogEntry:
    """Represents a single entry from a topic's log, generated from its surrounding ``<li>`` tag.

    :ivar str user: The responsible curator's username.
    :ivar str timestamp: The entry's timestamp.
    :ivar TildesTopicLogEntryKind kind: The kind of log entry.
    :ivar Optional[Dict] data: The data associated with this log entry. See `below <#tildee.TildesTopicLogEntryKind>`_ for structure."""

    def __init__(self, text):
        self._tree = html.fromstring(text)
        self.user = self._tree.cssselect("a.link-user")[0].text
        self.timestamp = self._tree.cssselect("span.topic-log-entry-time time")[
            0
        ].attrib["datetime"]
        edit_str = self._tree.cssselect("a.link-user")[0].tail.strip()
        self.kind = TildesTopicLogEntryKind.UNKNOWN
        self.data = None
        if edit_str.startswith("added tag") or edit_str.startswith("removed tag"):
            self.kind = TildesTopicLogEntryKind.TAG_EDIT
            added_tags = []
            removed_tags = []
            if "added tag '" in edit_str:
                # One added tag, find the phrase and extract the tag itself
                match = re.match("added tag '([a-z0-9. ]+)'", edit_str)
                added_tags = [match.group(1)]
            elif "added tags '" in edit_str:
                # Multiple tags, get the point where the removed tags part begins
                cutoff = edit_str.find("' and removed tag")
                if cutoff == -1:
                    # If we don't have a removed part, set the cutoff to the length of the input
                    cutoff = len(edit_str) - 1
                # Search for all tags in the input string within the cutoff
                # We add one to `cutoff` to include the final tag's closing _'_
                find_str = edit_str[: cutoff + 1]
                added_tags = re.findall("'([a-z0-9. ]+)'", find_str)
            if "removed tag '" in edit_str:
                # One removed tag, find the phrase and extract the tag itself
                # Can't use match — might not be start of string
                match = re.search("removed tag '([a-z0-9. ]+)'", edit_str)
                removed_tags = [match.group(1)]
            elif "removed tags '" in edit_str:
                # Multiple removed tags, find our start point and search from there
                start_point = edit_str.find("' and removed tag")
                # Add one to start_point to either exclude the final added tag's
                # closing _'_ or start from index 0
                find_str = edit_str[start_point + 1 :]
                removed_tags = re.findall("'([a-z0-9. ]+)'", find_str)
            self.data = {"added": added_tags, "removed": removed_tags}
        elif edit_str.startswith("changed link"):
            self.kind = TildesTopicLogEntryKind.LINK_EDIT
            match = re.match("changed link from (\\S+) to (\\S+)", edit_str)
            self.data = {"old": match.group(1), "new": match.group(2)}
        elif edit_str.startswith("changed title"):
            self.kind = TildesTopicLogEntryKind.TITLE_EDIT
            # BUG: If the string contains more than one _" to "_ sequence, i.e.
            # in any of the titles, this will not work correctly.
            # In that case we'll set a flag ("certain") to notify the user.
            certain = False
            if edit_str.count('" to "') == 1:
                certain = True
            match = re.match(
                'changed title from \\"([\\S ]+)\\" to \\"([\\S ]+)\\"', edit_str
            )
            self.data = {
                "old": match.group(1),
                "new": match.group(2),
                "certain": certain,
            }
        elif edit_str.startswith("unlocked comments"):
            self.kind = TildesTopicLogEntryKind.UNLOCK
        elif edit_str.startswith("locked comments"):
            self.kind = TildesTopicLogEntryKind.LOCK
        elif edit_str.startswith("un-removed"):
            self.kind = TildesTopicLogEntryKind.UNREMOVE
        elif edit_str.startswith("removed"):
            self.kind = TildesTopicLogEntryKind.REMOVE
        elif edit_str.startswith("moved"):
            self.kind = TildesTopicLogEntryKind.MOVE
            match = re.match("moved from ~(\\S+) to ~(\\S+)", edit_str)
            self.data = {"old": match.group(1), "new": match.group(2)}


class TildesTopicLogEntryKind(Enum):
    """Enum representing the possible kinds of topic log entry. Documentation includes structure for ``TildesTopicLogEntry``'s data attribute."""

    #: | Default option if the entry is unrecognized, no data.
    #: | data: ``None``
    UNKNOWN = auto()
    #: | Tag edit, data contains added and removed tags.
    #: | data: ``{"added": List[str], "removed": List[str]}``
    TAG_EDIT = auto()
    #: | Title edit, data contains old and new title. If the program can't decide what is part of the titles and what isn't, ``certain`` will be set to ``False``.
    #: | data: ``{"old": str, "new": str, "certain": bool}``
    TITLE_EDIT = auto()
    #: | Link edit, data contains old and new link.
    #: | data: ``{"old": str, "new": str}``
    LINK_EDIT = auto()
    #: | Group move, data contains old and new group path.
    #: | data: ``{"old": str, "new": str}``
    MOVE = auto()
    #: | Comments locked, no data.
    #: | data: ``None``
    LOCK = auto()
    #: | Comments unlocked, no data.
    #: | data: ``None``
    UNLOCK = auto()
    #: | Topic removed, no data.
    #: | data: ``None``
    REMOVE = auto()
    #: | Topic unremoved, no data.
    #: | data: ``None``
    UNREMOVE = auto()
