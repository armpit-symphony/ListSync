# Audit notes

These are the 29 October 2026 findings, checked again against this tree rather than accepted as diagnosis.

## `cryptography==41.0.8` could not be installed

Confirmed. `pip index versions cryptography` lists 41.0.7 and then 42.0.0. 41.0.8 is not on the index. The API requirements now pin `cryptography==44.0.3`, which installed in a clean virtualenv on Python 3.12. The pilot no longer uses Fernet at all, so this pin is only there because `python-jose` can import it. Payment-key encryption was removed with the payment paths.

## Frontend `ajv/dist/compile/codegen` on Node 25

Partly confirmed. With the Yarn lockfile, the hoisted package is `ajv` 6.12.6, and `require('ajv/dist/compile/codegen')` fails because that file belongs to ajv 8. `CI=true yarn build` still completed on Node.js 22.23.4 and on Node.js 25.2.1. The production build did not load that import. Bun was not installed, so a Bun-specific install was not reproduced. The supported command remains `yarn install --frozen-lockfile` and `yarn build`.

`@babel/plugin-proposal-private-property-in-object` is declared directly so the unmaintained Create React App preset is not depending on a package that happens to be present for another reason.

## Hardcoded JWT secret and default admin

Confirmed in the previous server. `SECRET_KEY` was the string `your-secret-key-change-in-production`, and startup inserted `admin@shopsync.com` with password `admin123`. Both are gone. The process refuses that secret and does not insert an admin user. `/api/admin/auth/login` returns 404 even if that email and password are posted. Tests cover this.

## Ephemeral payment encryption key and unsafe decrypt fallback

Confirmed in the previous server. `Fernet.generate_key()` ran on each process start, and `decrypt_data` returned the stored value when decryption failed. Those functions are deleted. Payment configuration is not written. Admin payment routes return 404. Stripe checkout and the webhook return 501 and do not read a card or a signing secret.

## CORS wildcard with credentials

Confirmed in the previous server (`allow_origins=["*"]` together with `allow_credentials=True`). Origins now come from `CORS_ORIGINS`, and a wildcard is a startup error. A browser preflight from `http://localhost:3000` is echoed back. A preflight from an unlisted origin does not receive `*` or that origin.

## Three-second item polling, and shared lists only after reload

Confirmed in the previous household screen: `setInterval(fetchItems, 3000)`, and the list index loaded once on mount. Both screens now subscribe to `GET /api/events` with the household bearer token. Writes publish `lists.changed` or `items.changed` to the owner and everyone the list is shared with. The browser test shared a list into a second session that was already on the index, then checked an item off in that session and saw the first session update, without a reload. The live API test asserts the item event arrives in under two seconds.
