from __future__ import annotations

from urllib.request import Request, urlopen

SOURCE_URL = "https://raw.githubusercontent.com/cmhart13-boop/OneMoreShiva/main/app.py"

request = Request(SOURCE_URL, headers={"User-Agent": "Draft-Coach-OneMoreShiva-Mirror"})
with urlopen(request, timeout=20) as response:
    source = response.read().decode("utf-8")

exec(compile(source, SOURCE_URL, "exec"), globals(), globals())
