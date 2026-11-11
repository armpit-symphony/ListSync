# Scope

ListSync in this branch is a household pilot. It is not a public production service, and a passing pilot check is not a launch approval.

## Implemented now

- Household registration and login, with passwords of at least 8 characters hashed with bcrypt.
- JWT signing key comes from `SECRET_KEY`. The old hardcoded secret is refused. Tokens last 24 hours unless `ACCESS_TOKEN_EXPIRE_MINUTES` is set.
- A household can create more than one list and share each list with more than one existing household account, by email.
- Members can add items, check them off, and delete them. Another member who has the list open, and a member sitting on the list index, sees those changes through a server-sent event stream from the one API process. If that stream drops, or its queue overflows, the page reloads its own lists and items when the stream connects again. It does not need a manual reload. A second worker is not supported.
- An account that was not invited gets the same response as a missing list. A retailer token is rejected with 403 on list routes.
- Items can record brand, package size, package unit, and quantity. Package units accept spelling aliases such as `ounces` to `oz`. Sizes are not converted across units, so 64 fl oz is not treated as 1 gallon or as 1 lb.
- A retailer can register and publish per-item example prices for their own store: amount, brand, package size, unit, optional validity window, and the store's city, state, and ZIP. Provenance is forced to `example`. A value of `live` is rejected. Expired windows are hidden. The household screen labels every amount `Example price` and says availability is not known.
- A price is called comparable only when the item name matches exactly and the brand, package size, and unit all match. A different brand or size is shown as not the same product.
- The household can store a city, state, and ZIP used only to label whether an example price is in the same ZIP, the same city, or another area. That location is not a shopping list and is not given to retailers as one.
- Whole-basket offers have an API and a screen that say they are not implemented and return no offers.
- Retailer monthly and yearly plans are named as future options. Creating a subscription, Stripe checkout, and Stripe webhooks return 501. Fee amounts are null. No card data is collected.
- The admin console routes return 404. The process does not create `admin@shopsync.com` / `admin123`.
- Outgoing email is not sent. Welcome mail and payment mail from the old server were removed from the running path.
- CORS allows only the origins in `CORS_ORIGINS`. `*` is refused, including with credentials.
- Shopping data is stored in MongoDB and is still there after the API process is stopped and started again.

## Left for later

- Charging retailers. Monthly and yearly billing, invoices, taxes, and dunning are not built. No fee number should be invented here.
- Live retailer inventory, sale prices, and any feed from a retailer's system.
- Whole-basket bids, totals, or fulfillment. Per-item example prices must not be added up and presented as a basket price.
- Password reset, email verification, and inviting someone who does not already have an account. Sharing finds an existing household user only.
- More than one API process sharing live events. The event stream is in memory in the one process that handled the write. A second worker would not see it.
- A rebuilt admin console. The old one is disabled rather than repaired.
- Account deletion, export, and a retention policy.
- Turning Docker into a verified production image. The Dockerfile still builds the frontend and API, and it will not start until `SECRET_KEY` and MongoDB are provided. That image was not run in this pilot.
