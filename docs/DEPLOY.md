# Deploy ListSync on the existing Ubuntu server

This runbook is for the DigitalOcean droplet that already serves sparkpitlabs.com, tntmemecoin.com, and wepocoin.org. ListSync stays beside those sites. It does not replace them.

Nothing in this repository contacts that server. Philip, or someone with a shell on the droplet, runs these steps.

## What is isolated

- Compose project name `listsync`.
- One Docker network and one named volume, `listsync_mongo`.
- MongoDB is not published on the host. It is not Postgres on 5432 and not Redis on 6379.
- The only new host port is `127.0.0.1:8510`. The read-only check did not show 8510 in use. Confirm again before boot.
- Host nginx matches only `listsync.sparkpitlabs.com`. Do not edit the existing site files.
- One uvicorn process. Do not raise `--workers`.

## What Philip decides

- The droplet's public IPv4 for the DNS record. This repo does not know it.
- That `8510` is still free when he deploys.
- Where the checkout lives. This runbook uses `/opt/listsync`.
- Backup directory and retention. The default is `/var/backups/listsync` and 14 days.
- The `SECRET_KEY` he generates on the server. It must not be committed.

## 1. DNS

Create an A record:

```
listsync.sparkpitlabs.com.   A   <droplet public IPv4>
```

Wait until `dig +short listsync.sparkpitlabs.com` shows that address from outside the droplet. Certbot will fail before this exists.

## 2. Checkout

```sh
sudo mkdir -p /opt/listsync
sudo chown "$USER" /opt/listsync
git clone <this repo> /opt/listsync
cd /opt/listsync
git checkout cursor/listsync-household-pilot-d317
```

Use the commit that contains `deploy/docker-compose.prod.yml`.

## 3. Environment file

```sh
cp deploy/.env.example deploy/.env
openssl rand -hex 32
```

Put that hex string in `SECRET_KEY`. Leave `CORS_ORIGINS` as `https://listsync.sparkpitlabs.com`. Leave `REACT_APP_BACKEND_URL` empty so the browser calls `/api` on the same host. `deploy/.env` stays on the server.

## 4. Boot the stack

```sh
cd /opt/listsync
docker compose -p listsync -f deploy/docker-compose.prod.yml --env-file deploy/.env up -d --build
docker compose -p listsync -f deploy/docker-compose.prod.yml ps
```

`docker compose ps` should show mongo, api, and web healthy. `ss -ltnp | grep 8510` should show `127.0.0.1:8510` only. There should be no new `0.0.0.0:27017`.

On the droplet, before nginx:

```sh
curl -fsS http://127.0.0.1:8510/api/health
```

The JSON includes `"status":"ok"` and `"billing_implemented":false`.

## 5. Certificate, then nginx

Confirm the other sites first:

```sh
ls /etc/nginx/sites-enabled
sudo nginx -t
```

Install the new site. Do not reload yet.

```sh
sudo mkdir -p /var/www/html
sudo cp deploy/nginx/listsync.sparkpitlabs.com.conf /etc/nginx/sites-available/listsync.sparkpitlabs.com
```

Issue the certificate with the webroot, while the HTTPS server block is not yet enabled. A simple way that does not touch the other sites:

```sh
sudo certbot certonly --webroot -w /var/www/html -d listsync.sparkpitlabs.com
```

That requires port 80 to reach this host. If the existing nginx already answers port 80, add only the port 80 server from the file first, run `sudo nginx -t`, reload, then run certbot. After the cert exists, install the full file.

```sh
sudo ln -s /etc/nginx/sites-available/listsync.sparkpitlabs.com /etc/nginx/sites-enabled/listsync.sparkpitlabs.com
sudo nginx -t && sudo systemctl reload nginx
```

If `nginx -t` fails, remove the new symlink and do not reload. The other sites stay on the previous config.

The HTTPS location proxies to `127.0.0.1:8510` with `proxy_buffering off` and a one-hour read timeout so the household event stream is not buffered.

## 6. Smoke test

From the droplet:

```sh
curl -fsS https://listsync.sparkpitlabs.com/api/health
```

From a phone not on the server: open `https://listsync.sparkpitlabs.com`, create a household account, create a list, share it with a second account that has already registered, and check an item off. The other phone, already on that list, should show the check without reload. The page should say Live.

A retailer account must not see that household list.

## 7. Two-phone gate

Do not call this a public launch after the curl check. The gate is two phones on cellular data, not the server's own browser:

1. Philip registers and creates the week's list.
2. His wife registers, then Philip shares the list to her email.
3. She opens the list. He adds an item. It shows on her phone without reload.
4. She checks it off. His phone shows the line struck through.
5. Restart only the api container: `docker compose -p listsync -f deploy/docker-compose.prod.yml restart api`. The list is still there after both phones reload once. Live updates resume after the stream reconnects.

## 8. Backup

```sh
sudo mkdir -p /var/backups/listsync
sudo chown "$USER" /var/backups/listsync
BACKUP_DIR=/var/backups/listsync RETENTION=14 /opt/listsync/deploy/backup.sh
```

Cron, as the user that can run Docker:

```
15 3 * * * cd /opt/listsync && BACKUP_DIR=/var/backups/listsync RETENTION=14 ./deploy/backup.sh >> /var/log/listsync-backup.log 2>&1
```

Restore practice, which loads a scratch database and does not replace the live one:

```sh
/opt/listsync/deploy/restore.sh /var/backups/listsync/listsync-YYYYMMDDTHHMMSSZ.archive.gz
```

The script prints counts for users, shopping lists, items, store users, and store products. It exits non-zero if scratch does not match live. Restoring over the live database requires `RESTORE_LIVE=yes` and the live database name as the second argument. Do not do that as a drill.

## 9. Rollback

Application only:

```sh
cd /opt/listsync
git checkout <previous-good-sha>
docker compose -p listsync -f deploy/docker-compose.prod.yml --env-file deploy/.env up -d --build
```

The volume `listsync_mongo` is kept.

Take the site off nginx without stopping the other sites:

```sh
sudo rm /etc/nginx/sites-enabled/listsync.sparkpitlabs.com
sudo nginx -t && sudo systemctl reload nginx
docker compose -p listsync -f deploy/docker-compose.prod.yml stop
```

## 10. What not to do

- Do not publish MongoDB.
- Do not set uvicorn `--workers` above 1.
- Do not point this server block at ports 3001, 3002, 8000, 8002, 8400, or 11434.
- Do not put ListSync environment variables into the Sparkbot or token-site env files.
- Do not commit `deploy/.env`.
