# Work log

## 2026-11-05

Continued the existing ListSync FastAPI and React app from commit `fd7739982ed02fcda8028ccbb5dd635648f1ba99` on a new branch. Did not replace the stack.

Checked the October audit against the code and the package index. `cryptography==41.0.8` is not published. The hoisted frontend `ajv` is 6.12.6, so `ajv/dist/compile/codegen` does not resolve, but `yarn build` still succeeds on Node 22 and Node 25. The hardcoded JWT secret, the default admin user, the per-process payment cipher with a fallback that returned ciphertext as plaintext, wildcard CORS with credentials, the three-second item poll, and the one-shot list load were all present and were changed.

Pilot behavior now: household register, login, create, share, add, check off, and delete, with server-sent events so the other session updates without a reload. Retailer accounts can store local example prices with brand, package size, unit, validity, and store locality. Comparable means those fields match. Units are not converted. Whole-basket offers and retailer billing stay explicit placeholders with no fee amounts. Admin, Stripe, PayPal, and outgoing mail are not on the running path. Lists stay off retailer tokens.

Tests and a two-session browser pass against the production build are recorded in `docs/EVIDENCE.md`. MongoDB 8.0.12 was installed locally because it was not already on the machine. No external account, email provider, or payment provider was used.

## 2026-11-06

Restyled the household pages as a lined notebook. Each item is a ruled line with a checkbox and a Prices dropdown. Checking the box keeps the line on the page and draws a line through the writing. The dropdown shows example retailer prices and whether the package actually matches. Retailer screens, privacy, and the live event stream are unchanged.

## 2026-11-09

Added GitHub Actions for the pytest suite against MongoDB 8 and a Node 22 production build. No host or domain was set up.

Fixed one-process live updates so a dropped stream or a full queue reloads that household's own lists and items from the API. The reload ignores an older response if a newer one is already in flight. Overflow no longer drops the last signal. Retailer accounts still cannot open the event stream. Notebook layout was left as approved.

Signed: Shoppy | 2026-11-05
Signed: Shoppy | 2026-11-06
Signed: Shoppy | 2026-11-09
