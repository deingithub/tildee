This is tildee.py, a Python 3 library for interacting with the <https://tildes.net> API. Note that this API is not stable and not actually intended for external use, so this could break at any moment.

## Capabilities
Currently tildee.py can parse posts and their comments, create comments, topics and messages, parse new messages and notifications, edit comment and topic contents, edit topic metadata and remove/lock topics and comments.

## Dependencies
This uses [Poetry](https://poetry.eustace.io/) to manage dependencies and [Black](https://black.readthedocs.io/en/stable/index.html#) for formatting.

## Development
To install dependencies, run `poetry install`. You can run a python shell in the environment using `poetry run python` (I'd recommend using `ipython`, too). Format your code before committing by running `black .`.
