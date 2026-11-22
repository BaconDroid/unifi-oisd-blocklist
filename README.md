# UniFi OISD Blocklist

Daily-generated UniFi Content Filter blocklist based on OISD Small. The
published list removes domains from OISD NSFW and keeps only domains whose
final suffix has exactly three characters.

The UniFi file format and initial idea were inspired by
[Unifi-Content-Filter-Blocklist](https://github.com/zombiehunternr1/Unifi-Content-Filter-Blocklist).
This repository is an independent implementation with automatic OISD updates.

`convert-list.py` converts common domain-list formats to the format accepted by
UniFi Content Filter: one domain per line.

It accepts a local file or an HTTP(S) URL, including OISD's `domainswild`
feeds. It removes comments, hosts-file IP addresses, AdGuard delimiters,
wildcard prefixes, invalid values, and duplicate domains.

```sh
# Convert a downloaded list
python3 convert-list.py input.txt -o unifi-blocklist.txt

# Convert OISD directly
python3 convert-list.py https://small.oisd.nl/domainswild -o unifi-oisd-small.txt

# Exclude selected country-code suffixes from the generated file
python3 convert-list.py https://small.oisd.nl/domainswild \
  --exclude-suffix .ru --exclude-suffix .cn \
  -o unifi-oisd-small-without-ru-cn.txt

# Configuration correspondant aux 15 pays à exclure
python3 convert-list.py https://small.oisd.nl/domainswild \
  --exclude-suffix .in --exclude-suffix .tr --exclude-suffix .ir \
  --exclude-suffix .ru --exclude-suffix .cn --exclude-suffix .kp \
  --exclude-suffix .by --exclude-suffix .ua --exclude-suffix .ng \
  --exclude-suffix .br --exclude-suffix .bd --exclude-suffix .iq \
  --exclude-suffix .lt --exclude-suffix .bg --exclude-suffix .np \
  -o unifi-oisd-small.txt

# Version recommandée : pays sélectionnés, suffixes de moins de 3 caractères
# et domaines présents dans la liste OISD NSFW complète
python3 convert-list.py https://small.oisd.nl/domainswild \
  --exclude-short-suffixes \
  --exclude-list https://nsfw.oisd.nl/domainswild \
  --exclude-suffix .in --exclude-suffix .tr --exclude-suffix .ir \
  --exclude-suffix .ru --exclude-suffix .cn --exclude-suffix .kp \
  --exclude-suffix .by --exclude-suffix .ua --exclude-suffix .ng \
  --exclude-suffix .br --exclude-suffix .bd --exclude-suffix .iq \
  --exclude-suffix .lt --exclude-suffix .bg --exclude-suffix .np \
  -o unifi-oisd-small-final.txt

# Keep only domains whose final suffix has exactly 3 characters
python3 convert-list.py https://small.oisd.nl/domainswild \
  --exclude-list https://nsfw.oisd.nl/domainswild \
  --exact-suffix-length 3 \
  -o unifi-oisd-small-final.txt

# Or read from stdin
cat input.txt | python3 convert-list.py - -o unifi-blocklist.txt
```

The converter writes statistics to stderr and the converted list to stdout
unless `--output` is supplied. OISD's `big` feed is much larger than the
custom list shown in the source repository, so `small` is a safer starting
point for UniFi testing. Suffix exclusions are optional and apply to the
suffix itself and its subdomains; they do not remove domains hosted in a
country but using a different top-level domain.


## Daily update

`.github/workflows/update.yml` runs on `workflow_dispatch` and on a daily cron
at `0 17 * * *` (17:00 UTC). It runs the `--exact-suffix-length 3` command
above (OISD Small minus OISD NSFW) and commits and pushes
`unifi-oisd-small-final-YYYY-MM-DD.txt` and the stable alias
`unifi-oisd-small-final.txt` only when the list changed. The dated filename
uses UTC; the previous dated snapshot is removed on each update.

Timezone limit: GitHub Actions cron is always UTC and has no DST support.
17:00 UTC is noon in EST (UTC-5, winter) but 13:00 in EDT (UTC-4, summer).
Scheduled runs can also start several minutes late under load.
