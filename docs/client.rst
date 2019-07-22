Client Usage
============

General
-------

All methods of the ``TildesClient`` raise if any exception occurs, including unsuccessful HTTP responses from the site.


Logging in
----------

You can connect to Tildes and log in by creating a new ``TildesClient`` instance and passing the login data to the constructor. If you're not connecting to tildes.net, override the ``base_url`` argument. If you're connecting to a local development instance, which uses self-signed SSL certificates, also pass ``verify_ssl = False`` to avoid errors. The automatic ratelimiting is set to 0.5 seconds between each request, but you can adjust it using the ``ratelimit`` parameter. Keep in mind that some actions, like posting topics or comments, are additionally ratelimited, see the `Tildes Source Code <https://gitlab.com/tildes/tildes/blob/master/tildes/tildes/lib/ratelimit.py#L283>`_.

.. autoclass:: tildee.TildesClient

.. code-block::

	from tildee import TildesClient
	t = TildesClient("username", "password")

Posting topics and comments
---------------------------

You can use the ``create_topic()`` and ``create_comment()`` methods for these tasks. They both return the new item's id36, which you can use for further operations or just … discard.

.. autofunction:: tildee.TildesClient.create_topic

.. autofunction:: tildee.TildesClient.create_comment

.. code-block::

	topic_id = t.create_topic("test", "Test Post Please Ignore", [], link = "https://example.com")
	top_level_comment_id = t.create_comment(topic_id, "I am a top level comment.")
	reply_comment_id = t.create_comment(top_level_comment_id, "I am a reply", top_level = False)

Fetching topics and comments
----------------------------

If you want to use data from comments or topics, you can use Tildee to fetch them and extract their data from the raw HTML the site returns. For more information and examples on these representations see the :doc:`models` page.

.. autofunction:: tildee.TildesClient.fetch_topic

.. autofunction:: tildee.TildesClient.fetch_comment


Fetching topic listings
-----------------------

If you either want to fetch topic listings for tags and/or groups or search for a phrase, use the ``fetch_filtered_topic_listing`` or the ``fetch_search_topic_listing`` method. Note that they only return the limited data the topic listing page offers.

.. autofunction:: tildee.TildesClient.fetch_filtered_topic_listing

.. autofunction:: tildee.TildesClient.fetch_search_topic_listing

Interacting with groups
-----------------------

To see what groups your account is subscribed to and which others are available, use ``fetch_groups``, it returns a list of ``TildesGroup``	instances. For details on these see the :doc:`models` page. To (un)subscribe from a group, use the ``set_group_subscription`` method.

.. autofunction:: tildee.TildesClient.fetch_groups

.. autofunction:: tildee.TildesClient.set_group_subscription

Interacting with topics
-----------------------

You can use Tildee to edit a topic's metadata, e.g. its tags or title (assuming your account has the permissions for this), edit or delete your account's own topics, and remove or lock topics if your account has admin permissions.

.. autofunction:: tildee.TildesClient.edit_topic

.. autofunction:: tildee.TildesClient.delete_topic

.. autofunction:: tildee.TildesClient.moderate_topic

.. code-block::

	t.edit_topic("bna", tags=["example.tag"], vote = True)
	t.delete_topic("f0s")
	t.moderate_topic("ct2", remove = False)

Interacting with comments
-------------------------

You can use Tildee to interact with comments, i.e. editing and deleting your account's own, voting on and labeling other's, bookmarking, and — given admin permissions — removing them.

.. autofunction:: tildee.TildesClient.edit_comment

.. autofunction:: tildee.TildesClient.edit_comment_labels

.. autofunction:: tildee.TildesClient.delete_comment

.. autofunction:: tildee.TildesClient.moderate_comment

.. code-block::

	t.edit_comment("9hr", bookmark = True)
	t.delete_comment("2bve")
	t.moderate_comment("2k8b", remove = True)

Notifications
-------------

Notifications are created by comments when they're in reply to one of your comments/topics or your account is @-mentioned in their text. You can fetch unread notifications as ``TildesNotification`` objects using ``fetch_unread_notifications()``, for more on these see the :doc:`models` page. Use the ``mark_notification_as_read()`` method to mark a notification as read.

.. autofunction:: tildee.TildesClient.fetch_unread_notifications

.. autofunction:: tildee.TildesClient.mark_notification_as_read

Sending messages
----------------

You can send messages in existing conversations using ``create_message()`` or create conversations using the aptly named ``create_conversation()``.

.. autofunction:: tildee.TildesClient.create_message

.. autofunction:: tildee.TildesClient.create_conversation

Fetching messages and conversations
-----------------------------------

To check for new messages, use the ``fetch_unread_message_ids()`` method which returns a list of message id36s. You can then use ``fetch_conversation()`` to fetch and process them individually. A conversation is represented by a ``TildesConversation`` object, which has a list of children ``TildesMessage`` objects. For details on these see the :doc:`models` page.

.. autofunction:: tildee.TildesClient.fetch_unread_message_ids

.. autofunction:: tildee.TildesClient.fetch_conversation

.. code-block::

	new_messages = t.fetch_unread_message_ids()
	for convo_id36 in new_messages:
		convo = t.fetch_conversation(convo_id36)
		# Do things here
		time.sleep(1)

Interacting with group wikis
----------------------------

You can fetch a group wiki page using ``fetch_wiki_page``, and, if you have editing permissions, its underlying markdown code using ``fetch_wiki_page_markdown``. Fetch a list of all wiki pages in a group using ``fetch_wiki_page_list`` and edit/create new pages using ``edit_wiki_page`` and ``create_wiki_page``, respectively.

.. autofunction:: tildee.TildesClient.fetch_wiki_page_list

.. autofunction:: tildee.TildesClient.fetch_wiki_page

.. autofunction:: tildee.TildesClient.fetch_wiki_page_markdown

.. autofunction:: tildee.TildesClient.edit_wiki_page

.. autofunction:: tildee.TildesClient.create_wiki_page