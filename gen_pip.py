import urllib.request
import json
import sys

deps = ['tinify', 'requests', 'urllib3', 'idna', 'charset-normalizer', 'certifi']
sources = []

for dep in deps:
    req = urllib.request.Request(f'https://pypi.org/pypi/{dep}/json')
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        version = data['info']['version']
        releases = data['releases'][version]
        # Prefer sdist (tar.gz) for better cross-platform support during flatpak build
        release = next((r for r in releases if r['packagetype'] == 'sdist'), releases[0])
        sources.append({
            "type": "file",
            "url": release['url'],
            "sha256": release['digests']['sha256']
        })

manifest = {
    "name": "python3-tinify",
    "buildsystem": "simple",
    "build-commands": [
        "pip3 install --verbose --exists-action=i --no-index --find-links=\"file://${PWD}\" --prefix=${FLATPAK_DEST} tinify"
    ],
    "sources": sources
}

print(json.dumps(manifest, indent=4))
