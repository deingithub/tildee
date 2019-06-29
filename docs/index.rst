.. tildee documentation master file, created by
   sphinx-quickstart on Sat Jun 29 14:38:24 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to tildee's documentation!
==================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

This is tildee.py, a Python 3 library for interacting with the <https://tildes.net> API. Note that this API is not stable and not actually intended for external use, so this could break at any moment.

`Source code <https://git.dingenskirchen.systems/Dingens/tildee.py>`_ and `issue tracker <https://git.dingenskirchen.systems/Dingens/tildee.py/issues>`_ on Dingenskirchen Git

Capabilities
------------

Currently tildee.py can parse posts and their comments, create comments, topics and messages, parse new messages and notifications, edit comment and topic contents, edit topic metadata, delete, remove and lock topics and comments.

Development
----------

To install dependencies, run `poetry install`. You can run a python shell in the environment using `poetry run python` (I'd recommend using `ipython`, too). Format your code before committing by running `black .`.

License
-------

The project is licensed under the MIT license.

.. autoclass:: tildee.TildesClient
   :members:
