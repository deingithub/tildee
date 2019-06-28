This is tildee.py, a Python 3 library for interacting with the <https://tildes.net> API. Note that this API is not stable and not actually intended for external use, so this could break at any moment.

**Dependencies**
 - requests
 - lxml
 - cssselect

This uses [Poetry](https://poetry.eustace.io/) to manage dependencies and [Black](https://black.readthedocs.io/en/stable/index.html#) for formatting.

To install dependencies, run `poetry install`. You can run a python shell in the environment using `poetry run python` (I'd recommend using `ipython`, too). Format your code before committing by running `black .`.

**Todo**
 - Tests if I find a way to do this meaningfully
