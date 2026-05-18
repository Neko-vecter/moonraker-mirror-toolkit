# moonraker mirror toolkit

## init

```shell
cd ~/mmt
make init

chmod +x git-repo.sh
```

## config example

config is based on [tunasync](https://github.com/tuna/tunasync)

### tunasync `worker.conf`

```toml title="worker.conf"
[[mirrors]]
name = "mainsail-release"
provider = "command"
upstream = ""
command = "/path-venv/python3 /path/mmt/sync-webui-release.py --workers 5 --config /path/mainsail-mirror.json"
size_pattern = "Total size is ([0-9\\.]+[KMGTP]?)"
interval = 720

[[mirrors]]
name = "klipper.git"
provider = "command"
command = "/path/mmt/git-repo.sh -b master"
upstream = "https://github.com/Klipper3d/klipper.git"
size_pattern = "Total size is ([0-9.]+[KMGTP]?)"
interval = 720

[[mirrors]]
name = "moonraker.git"
provider = "command"
command = "/path/mmt/git-repo.sh -b master"
upstream = "https://github.com/Neko-vecter/moonraker.git"
size_pattern = "Total size is ([0-9.]+[KMGTP]?)"
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
