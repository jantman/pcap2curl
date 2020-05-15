#!/usr/bin/env python

import sys
from scapy.all import PcapReader, re, Raw, TCP


VALID_METHODS = [
    "GET",
    b'GET',
    "HEAD",
    "POST",
    "PUT",
    "DELETE",
    "CONNECT",
    "OPTIONS",
    "TRACE",
    "PATCH"
]  # see https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods

def payload2curl(p):
    lines = re.compile(b"[\n\r]+").split(p)
    start_line = re.search(b"^([A-Z]+) ([^ ]+) (HTTP\/[0-9\/]+)", lines[0])
    method = start_line.group(1)
    url = start_line.group(2)
    version = start_line.group(3)  # Never used

    if method not in VALID_METHODS:
        sys.stderr.write(f'Method not valid: {method}\n')
        return

    del lines[0]
    headers = []
    for line in lines:
        if b":" in line:
            headers.append("-H '{}'".format(line))
        if b"Host:" in line:
            host_header = re.search(b"^Host: (.*)", line)
            host_name = host_header.group(1)

    proto_host = b'http://' + host_name + b'/'
    if not url.startswith(proto_host):
        url = "{}{}".format(proto_host, url[1:] if url[0] == "/" else url)
    curl = "curl '{}' \\\n -X {} \\\n ".format(url, method)
    curl += " \\\n ".join(headers)
    return curl


def main():
    if len(sys.argv) != 2:
        print ("I need an input file. Usage ./pcap2curl.py inputfilename")
        return

    infile = sys.argv[1]

    with PcapReader(infile) as packets:
        for p in packets:
            if p.haslayer(TCP) and p.haslayer(Raw) and p[TCP].dport == 80:
                payload = p[Raw].load
                cmd = payload2curl(payload)
                if cmd:
                    print(cmd)


if __name__ == "__main__":
    main()
