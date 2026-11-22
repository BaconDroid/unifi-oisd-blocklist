#!/usr/bin/env python3
"""Convert common domain-list formats to UniFi Content Filter format.

The output contains one domain per line, without comments, hosts-file IPs,
AdGuard delimiters, wildcard prefixes, or duplicate entries.
"""

from __future__ import annotations

import argparse
import ipaddress
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?$",
    re.IGNORECASE,
)


def read_source(source: str) -> tuple[str, str]:
    if source == "-":
        return sys.stdin.read(), "stdin"
    if source.startswith(("http://", "https://")):
        request = Request(source, headers={"User-Agent": "unifi-list-converter/1.0"})
        with urlopen(request, timeout=60) as response:  # noqa: S310 - explicit http(s) input
            return response.read().decode("utf-8", "replace"), source

    path = Path(source)
    return path.read_text(encoding="utf-8-sig"), str(path)


def clean_domain(line: str) -> str | None:
    line = line.strip().lower().rstrip(".")
    if not line or line.startswith(("#", "!", ";")):
        return None

    # Remove inline comments used by hosts files and simple domain lists.
    line = line.split("#", 1)[0].strip()
    if not line:
        return None

    # Hosts format: 0.0.0.0 example.com or ::1 example.com.
    fields = line.split()
    if len(fields) >= 2:
        try:
            ipaddress.ip_address(fields[0])
        except ValueError:
            pass
        else:
            line = fields[1]

    # AdGuard/uBlock formats and OISD's domainswild format.
    line = line.removeprefix("||").removeprefix("*.")
    line = line.split("^", 1)[0]
    line = line.split("$", 1)[0]

    # Accept a URL when a source contains full URLs instead of domains.
    if "://" in line:
        line = urlparse(line).hostname or ""
    else:
        line = line.split("/", 1)[0].split(":", 1)[0]

    if line.startswith("www."):
        line = line[4:]
    if not line or "." not in line:
        return None
    try:
        if ipaddress.ip_address(line):
            return None
    except ValueError:
        pass
    return line if DOMAIN_RE.fullmatch(line) else None


def normalize_suffix(suffix: str) -> str:
    suffix = suffix.strip().lower()
    return suffix if suffix.startswith(".") else f".{suffix}"


def domains_from_text(text: str) -> set[str]:
    return {
        domain
        for line in text.splitlines()
        if (domain := clean_domain(line)) is not None
    }


def convert(
    text: str,
    excluded_suffixes: set[str] | None = None,
    excluded_domains: set[str] | None = None,
    exclude_short_suffixes: bool = False,
    exact_suffix_length: int | None = None,
) -> tuple[list[str], int, int, int, int]:
    domains: set[str] = set()
    ignored = 0
    excluded = 0
    excluded_by_list = 0
    nonempty = 0
    excluded_suffixes = excluded_suffixes or set()
    excluded_domains = excluded_domains or set()
    for raw_line in text.splitlines():
        if raw_line.strip():
            nonempty += 1
        domain = clean_domain(raw_line)
        if domain:
            tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
            if domain in excluded_domains:
                excluded_by_list += 1
            elif (
                any(domain.endswith(suffix) for suffix in excluded_suffixes)
                or (exclude_short_suffixes and len(tld) < 3)
                or (exact_suffix_length is not None and len(tld) != exact_suffix_length)
            ):
                excluded += 1
            else:
                domains.add(domain)
        elif raw_line.strip() and not raw_line.lstrip().startswith(("#", "!", ";")):
            ignored += 1
    return sorted(domains), nonempty, ignored, excluded, excluded_by_list


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid integer: {value!r}") from None
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="local file or http(s) URL")
    parser.add_argument("-o", "--output", help="output file; stdout when omitted")
    parser.add_argument(
        "--exclude-suffix",
        action="append",
        default=[],
        metavar="TLD",
        help="exclude a country or domain suffix (repeatable, e.g. --exclude-suffix .ru)",
    )
    parser.add_argument(
        "--exclude-list",
        action="append",
        default=[],
        metavar="FILE_OR_URL",
        help="exclude domains found in a local file or HTTP(S) URL (repeatable)",
    )
    parser.add_argument(
        "--exclude-short-suffixes",
        action="store_true",
        help="exclude domains whose final suffix is shorter than three characters",
    )
    parser.add_argument(
        "--exact-suffix-length",
        type=positive_int,
        metavar="N",
        help="keep only domains whose final suffix has exactly N characters (e.g. 3)",
    )
    args = parser.parse_args()

    try:
        text, source_name = read_source(args.source)
        suffixes = {normalize_suffix(value) for value in args.exclude_suffix}
        excluded_domains: set[str] = set()
        for excluded_source in args.exclude_list:
            excluded_text, _ = read_source(excluded_source)
            excluded_domains.update(domains_from_text(excluded_text))
        domains, nonempty, ignored, excluded, excluded_by_list = convert(
            text,
            suffixes,
            excluded_domains,
            args.exclude_short_suffixes,
            args.exact_suffix_length,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    result = "\n".join(domains) + ("\n" if domains else "")
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
    else:
        sys.stdout.write(result)

    print(
        f"Converted {source_name}: {len(domains)} domains, "
        f"{nonempty} non-empty lines, {ignored} ignored lines, "
        f"{excluded} excluded by suffix, {excluded_by_list} excluded by list.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
