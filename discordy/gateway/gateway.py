from urllib.parse import urlencode


class Gateway:
    def __init__(self, **options) -> None:
        self.base_url = options["url"]
        self.shards = options.get("shards", 1)

        self.version = options.get("version", 9)
        self.encoding = options.get("encoding", "json")
        self.compress = options.get("compress", "zlib-stream")

    @property
    def url(self) -> str:
        queries = {'v': self.version, "encoding": self.encoding}

        if self.compress:
            queries["compress"] = self.compress

        return self.base_url + '?' + urlencode(queries)
