# UniFi OISD Blocklist

Daily-generated blocklist for the UniFi Content Filter. The published list is
generated from [OISD Small](https://oisd.nl/), removes domains present in the
[OISD NSFW list](https://nsfw.oisd.nl/domainswild), and keeps domains whose
final suffix is between three and five characters long.

The UniFi file format and the initial idea were inspired by
[Unifi-Content-Filter-Blocklist](https://github.com/zombiehunternr1/Unifi-Content-Filter-Blocklist).
This is an independent implementation with automated OISD updates.

## Use with UniFi

Use the stable URL below in UniFi. It always points to the latest generated
list:

```text
https://raw.githubusercontent.com/BaconDroid/unifi-oisd-blocklist/main/unifi-oisd-small-final.txt
```

The repository also publishes a dated snapshot, for example:

```text
https://raw.githubusercontent.com/BaconDroid/unifi-oisd-blocklist/main/unifi-oisd-small-final-2026-11-22.txt
```

The current generated list contains approximately 47,000 unique domains and
is kept below 1 MB. The exact count changes as OISD is updated.

## Converter

`convert-list.py` converts common domain-list formats to the UniFi format: one
domain per line. It accepts a local file, standard input, or an HTTP(S) URL.
It removes comments, hosts-file IP addresses, AdGuard delimiters, wildcard
prefixes, invalid values, and duplicates.

```sh
# Convert a local file
python3 convert-list.py input.txt -o unifi-blocklist.txt

# Convert OISD Small and exclude the OISD NSFW list
python3 convert-list.py https://small.oisd.nl/domainswild \
  --exclude-list https://nsfw.oisd.nl/domainswild \
  --min-suffix-length 3 \
  --max-suffix-length 5 \
  -o unifi-oisd-small-final.txt

# Read from standard input
cat input.txt | python3 convert-list.py - -o unifi-blocklist.txt
```

The converter writes statistics to stderr and the converted list to stdout
unless `--output` is supplied. Suffix filters apply to the final suffix and
its subdomains; they do not identify where a domain is physically hosted.

## Daily update

`.github/workflows/update.yml` runs on `workflow_dispatch` and daily at
`17:00 UTC` (`0 17 * * *`). It downloads OISD Small and OISD NSFW, generates
the list, writes `unifi-oisd-small-final-YYYY-MM-DD.txt`, updates the stable
`unifi-oisd-small-final.txt` alias, and commits only when the output changes.
The previous dated snapshot is removed on each update.

GitHub Actions schedules use UTC and do not adjust for daylight saving time.
`17:00 UTC` is noon in EST (UTC-5) and 13:00 in EDT (UTC-4). Scheduled runs
may also start a few minutes late under GitHub load.

## Credits

- [OISD](https://oisd.nl/) provides the source lists.
- [Unifi-Content-Filter-Blocklist](https://github.com/zombiehunternr1/Unifi-Content-Filter-Blocklist)
  inspired the UniFi format and project direction.
