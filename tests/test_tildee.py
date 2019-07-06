from tildee.models import *


def test_topic_log_parser_links():
    input = """<li class="topic-log-entry">
              <a href="/user/TestUser" class="link-user">TestUser</a>
            changed link from https://example.com to https://example.com/a
            <span class="topic-log-entry-time">(<time datetime="2019-06-28T16:23:23Z" title="2019-06-28 16:23:23 UTC">5d 1h ago</time>)</span>
          </li>"""
    output = TildesTopicLogEntry(input)
    assert output.kind == TildesTopicLogEntryKind.LINK_EDIT
    assert output.data["old"] == "https://example.com"
    assert output.data["new"] == "https://example.com/a"


def test_topic_log_parser_titles_safe():
    input = """<li class="topic-log-entry">
              <a href="/user/TestUser" class="link-user">TestUser</a>
            changed title from "More tests? Yes." to "More tests? Yes. No."
            <span class="topic-log-entry-time">(<time datetime="2019-06-28T16:21:24Z" title="2019-06-28 16:21:24 UTC">5d 1h ago</time>)</span>
          </li>"""
    output = TildesTopicLogEntry(input)
    assert output.kind == TildesTopicLogEntryKind.TITLE_EDIT
    assert output.data["certain"] == True
    assert output.data["old"] == "More tests? Yes."
    assert output.data["new"] == "More tests? Yes. No."


def test_topic_log_parser_titles_unsafe():
    input = """<li class="topic-log-entry">
              <a href="/user/TestUser" class="link-user">TestUser</a>
            changed title from "A bc" to "A bc " to "blorb""
            <span class="topic-log-entry-time">(<time datetime="2019-06-30T16:08:54Z" title="2019-06-30 16:08:54 UTC">3d 1h ago</time>)</span>
          </li>"""
    output = TildesTopicLogEntry(input)
    assert output.kind == TildesTopicLogEntryKind.TITLE_EDIT
    assert output.data["certain"] == False
