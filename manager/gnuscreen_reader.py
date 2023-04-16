import os
import re
from typing import Generator, Type, Callable

__all__ = ["TermReadParser", "LineTermReadParser", "read"]


class TermReadParser:
    _read: Callable[[], Generator[bytes, None, None]]

    def read(self) -> Generator[bytes, None, None]:
        return self._read()


class LineTermReadParser(TermReadParser):
    LINE_REGEX = re.compile(rb"\x08(.+)\r")

    def read(self) -> Generator[bytes, None, None]:
        buf = b""
        for chunk in self._read():
            buf += chunk
            m = self.LINE_REGEX.search(buf)
            while m:
                yield m.group(1)
                buf = buf[m.end(1) + 1:]
                m = self.LINE_REGEX.search(buf)


def read(fd, *, chunk_size=1024, cls: Type[TermReadParser] = TermReadParser):
    def _read():
        try:
            chunk = os.read(fd, chunk_size)
            while chunk:
                yield chunk
                chunk = os.read(fd, chunk_size)
        except OSError:
            return

    parser = cls()
    parser._read = _read
    return parser.read()
