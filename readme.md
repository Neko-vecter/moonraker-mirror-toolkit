# moonraker mirror toolkit

## init venv

```shell
cd ~/mwmt
make init
```

## config example

config is based on [tunasync](https://github.com/tuna/tunasync)

### tunasync `worker.conf`

```systemd title="worker.conf"
[[mirrors]]
name = "mainsail-release"
provider = "command"
upstream = ""
command = "/path-venv/python3 /path/update-version.py --workers 5 --config /path/config.json"
size_pattern = "Total size is ([0-9\\.]+[KMGTP]?)"
interval = 720
```

### `config.json`

```json
{
    "repo": "owner/repo",
    "keep_versions": 10,
    "base_mirror_url": "<mirrors>/repo-release"
}
```
