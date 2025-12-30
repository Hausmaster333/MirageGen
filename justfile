format path=".":
    uv run ruff format {{ path }}

lint path=".":
    uv run ruff check --fix --unsafe-fixes {{ path }}
    uv run ruff format {{ path }}

typing path=".":
    uv run basedpyright {{ path }}
