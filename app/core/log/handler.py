import datetime
import logging
from logging.handlers import BaseRotatingHandler
from pathlib import Path


class LinRotatingFileHandler(BaseRotatingHandler):
    """RotatingFileHandler.

    from: https://pypi.org/project/Lin-CMS/
    The logs are saved in monthly folders, named after year and month, and each day is saved into a file named after
    the year, month, and day. Logs are rotated daily or when they exceed a specified maximum size, and are renamed to
    include the current time in case the filename already exists.

    Args:
        log_dir (Union[str, Path]): The path to the logs directory.
        mode (str): The default file mode for opening the log file.
        max_bytes (int): The maximum size of the rotated log files. Leave as 0 or lower to disable size limits.
        encoding (Optional[str]): The encoding used when writing to the log file.
        delay (bool): If True, the file is opened in 'delayed' mode, which defers creation until the first message is
            written.

    Attributes:
        _log_dir (Path): The resolved path to the logs directory.
        _suffix (str): File extension for the log files.
        _year_month (str): Current year and month, used in creating new log directories.
        store_dir (Path): Path to the currently active log directory.
        filename (str): Current year, month, and day, used in naming log files.
        max_bytes (int): Maximum size of the rotated log files.
    """

    def __init__(
        self,
        log_dir: str | Path = "logs",
        mode: str = "a",
        max_bytes: int = 0,
        encoding: str | None = None,
        delay: bool = False,
    ) -> None:
        if max_bytes > 0:
            mode = "a"
        self._log_dir = Path(log_dir).resolve()
        self._suffix = ".log"
        now = datetime.datetime.now(datetime.UTC)
        self._year_month = now.strftime("%Y-%m")
        self.store_dir = self._log_dir / self._year_month
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.filename = now.strftime("%Y-%m-%d")
        filename = self.store_dir / f"{self.filename}{self._suffix}"
        super().__init__(filename, mode, encoding, delay)
        self.max_bytes = max_bytes

    def doRollover(self) -> None:  # noqa
        now = datetime.datetime.now(datetime.UTC)
        year_month = now.strftime("%Y-%m")
        filename = now.strftime("%Y-%m-%d")

        if self.stream:
            self.stream.close()
            del self.stream

        if self.filename != filename or self._year_month != year_month:
            self.baseFilename = str(self._log_dir / year_month / filename / self._suffix)
            self._year_month = year_month
            self.filename = filename
        else:
            dfn = self.rotation_filename(
                self.baseFilename.replace(
                    self._suffix,
                    "-" + now.strftime("%H-%M-%S") + self._suffix,
                )
            )
            Path(dfn).unlink(missing_ok=True)
            self.rotate(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()

    def shouldRollover(self, record: logging.LogRecord) -> bool:  # noqa
        """Determine if a rollover should occur."""
        now = datetime.datetime.now(datetime.UTC)
        year_month = now.strftime("%Y-%m")
        filename = now.strftime("%Y-%m-%d")

        if self._year_month != year_month or self.filename != filename:
            return True
        if self.max_bytes > 0:
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)
            if self.stream.tell() + len(msg) > self.max_bytes:
                return True
        return False
