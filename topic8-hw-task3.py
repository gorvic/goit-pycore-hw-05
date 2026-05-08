import re
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Final, Optional

# sys.argv.append("topic8-hw-task3.log")
# sys.argv.append("all")


class LogRowLevel(StrEnum):
    """Supported log levels."""

    INFO = "INFO"
    DEBUG = "DEBUG"
    ERROR = "ERROR"
    WARNING = "WARNING"

    @classmethod
    def has(cls, level: str) -> bool:
        """Return True if level is supported."""
        return level.strip().upper() in cls.__members__


LOG_ROW_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\s*(?P<date>\d{4}-\d{2}-\d{2})"
    r"\s+"
    r"(?P<time>\d{2}:\d{2}:\d{2})"
    r"\s+"
    rf"(?P<level>{'|'.join(LogRowLevel.__members__)})"
    r"\s+"
    r"(?P<message>.+?)\s*$"
)


@dataclass(frozen=True, slots=True)
class LogRow:
    """Represent one parsed log row."""

    level: LogRowLevel
    create_date: datetime
    message: str


def parse_log_line(line: str) -> dict[str, str]:
    """
    Parse one raw log line into dictionary.

    This function returns dict to match the task requirement. Conversion to
    LogRow is done later in load_logs().
    """

    return match.groupdict() if (match := LOG_ROW_PATTERN.match(line)) else {}


def make_log_row(data: dict[str, str]) -> LogRow:
    """
    Convert parsed log dictionary into LogRow object.
    """
    return LogRow(
        level=LogRowLevel(data["level"]),
        create_date=datetime.fromisoformat(f"{data['date']}T{data['time']}"),
        message=data["message"],
    )


def load_logs(file_path: str) -> list[LogRow]:
    """
    Load log rows from file.

    Invalid lines are skipped.
    """
    log_rows: list[LogRow] = []
    file = Path(file_path)

    if file.is_file():
        with file.open("r", encoding="utf-8") as handle:
            log_rows = [
                make_log_row(data)
                for line in handle
                if (data := parse_log_line(line))
            ]

    return log_rows


def filter_logs_by_level(logs: list[LogRow], level: str) -> list[LogRow]:
    """
    Return log rows matching the given level.
    """
    row_level = LogRowLevel(level.strip().upper())

    return [
        row
        for row in logs
        if row.level == row_level
    ]


def count_logs_by_level(logs: list[LogRow]) -> dict[str, int]:
    """
    Count log rows by log level.
    """
    counts = {level.value: 0 for level in LogRowLevel}

    for row in logs:
        counts[row.level.value] += 1

    return counts


def display_log_counts(counts: dict[str, int]) -> None:
    """
    Display log counters as an aligned table.
    """
    level_header = "Рівень логування"
    count_header = "Кількість"

    level_width = max(
        [len(level_header)] + [len(level) for level in counts]
    )

    count_width = max(
        [len(count_header)] + [len(str(count)) for count in counts.values()]
    )

    print(f"{level_header:<{level_width}} | {count_header:>{count_width}}")
    print(f"{'-' * level_width}-|-{'-' * count_width}")

    for level, count in counts.items():
        print(f"{level:<{level_width}} | {count:<{count_width}}")


def format_log_row(row: LogRow, show_level: bool = False) -> str:
    """
    Format one log row for console output.
    """
    level_prefix = f"{f'[{row.level.value}]':<9} " if show_level else ""

    result = (
        f"{level_prefix}"
        f"{row.create_date:%Y-%m-%d %H:%M:%S} "
        f"- {row.message}"
    )

    return result


def display_logs(logs: list[LogRow], level: Optional[str] = None) -> None:
    """
    Display detailed log rows.

    If level is not provided, all logs are displayed with level prefix.
    """
    normalized_level = level.strip().upper() if level and LogRowLevel.has(level) else None
    filtered_logs = (
        filter_logs_by_level(logs, normalized_level)
        if normalized_level
        else logs
    )

    header = "Деталі логів"

    if normalized_level:
        header += f" для рівня '{normalized_level}'"

    print(f"{header}:")

    for row in filtered_logs:
        print(format_log_row(row, show_level=normalized_level is None))


def main() -> None:
    """
    Run log analyzer CLI.
    """
    if len(sys.argv) > 1:
        logs = load_logs(sys.argv[1])
        counts = count_logs_by_level(logs)

        display_log_counts(counts)

        if len(sys.argv) > 2:
            level = sys.argv[2].strip()

            if level.lower() == "all":
                print()
                display_logs(logs)
            elif LogRowLevel.has(level):
                print()
                display_logs(logs, level)


if __name__ == "__main__":
    main()
