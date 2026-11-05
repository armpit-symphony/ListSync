# Evidence

Checked on 5 November 2026. This is a pilot record, not a production sign-off.

## Install and build

- `python3 -m venv` and `pip install -r backend/requirements-dev.txt` completed. That install resolved `cryptography==44.0.3`.
- `yarn install --frozen-lockfile` in `frontend/` completed after the lockfile update.
- `CI=true yarn build` completed on Node.js 22.23.4 and again on Node.js 25.2.1 (`v25.2.1` reported by the downloaded binary). The production bundle was `frontend/build/static/js/main.b4cddeb6.js`.

## API tests

Command:

```sh
python -m pytest tests/test_pilot_api.py tests/test_live_server.py -q
```

Result: `8 passed, 76 warnings in 5.79s`. The warnings are existing deprecations from `datetime.utcnow` and from libraries. No test failed.

Covered there:

- Refusing the old JWT secret, a short secret, and `CORS_ORIGINS=*`.
- Health, explicit CORS, disabled admin login, no default admin document, disabled payment config, Stripe checkout, webhook, and subscription purchase.
- Register, share, outsider 404, retailer 403, check off, delete, and a second MongoDB client reading the same item.
- Example prices: comparable only for the same brand, size, and unit; a gallon is not treated as fluid ounces; an expired window is omitted; `provenance=live` is rejected; a different product name is not matched; the basket payload is `implemented: false` and `offers: []`.
- A real uvicorn process on port 8765 delivers `lists.changed` and `items.changed` to the other household session. The item event in that run was under the test's two-second limit. After that process was killed and started again, the checked-off item was still in MongoDB.

## Browser

The production build was served at `http://127.0.0.1:3000` and the API at `http://127.0.0.1:8001` with database `listsync_browser`. `scripts/browser_household_flow.py` exited 0. It used two browser contexts plus an outsider and a retailer:

- Ada's context, already showing the list index and a Live status, gained "Weekly groceries" after Philip shared it. Viewport 390 by 844.
- Philip added Whole milk, Horizon, 64 fl oz. It showed up on Ada's open list. Ada checked it off. Philip's already open list showed it checked, with "2 members" and "Live".
- A third account saw "No lists yet".
- The retailer saved two example prices and opened a subscription panel whose monthly and yearly fees are Unset.
- Philip saved Austin / TX / 78701, turned example prices on, and saw the Horizon row as a comparable example and the store brand as not the same product. The basket box still said it is not implemented.

The API process was then stopped and started again with the same `SECRET_KEY` and the same database. A new browser signed in as Philip, opened the list, and still saw Whole milk and the example prices. Screenshot `10-after-api-restart.png`.

A separate desktop pass, after that restart, signed in as Philip and as Ada in an incognito window. Ada added Bananas, Dole, 3 lb. Philip's already open list showed Bananas, added by Ada, without a reload. No error text was shown. The screen recording is `listsync-live-share`.

Screenshots from that pass are in `docs/evidence/` and were also written to `/opt/cursor/artifacts/`.

## Not claimed

The Docker image was not booted. Bun was not used to build the frontend. No email was sent, no card was charged, and no retailer system was contacted. Two API workers were not tested; live updates are for the one process that received the write.
