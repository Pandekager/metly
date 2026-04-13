# Metly Shopify App

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Authenticate with Shopify:
   ```bash
   npm run shopify auth login
   ```

3. Run the app:
   ```bash
   npm run dev
   ```

## Demo Store Seed

This folder now includes a Shopify seed script that creates a realistic Metly golf demo store directly inside a Shopify dev store.

What it creates:
- 24 golf products across categories like drivers, irons, wedges, bags and balls
- 10 demo customers with Danish names and addresses
- 45 completed draft-order based demo orders
- inventory and unit cost values for seeded products

### Required app scopes

The app config includes the scopes needed for seeding:
- `write_products`
- `write_customers`
- `write_draft_orders`
- `write_inventory`

If you change scopes, run:
```bash
npm run push
```

and reinstall / update the app in the dev store so the token gets the new permissions.

### Environment

Create `shopify_app/.env` from `.env.example` and set:

```bash
SHOPIFY_DEMO_STORE=your-dev-store.myshopify.com
SHOPIFY_DEMO_ACCESS_TOKEN=shpat_...
SHOPIFY_API_VERSION=2025-10
```

### Run the seed

```bash
npm run seed:demo
```

After that, connect the same Shopify store in Metly and run:

```bash
./update-data.sh
```

to ingest the seeded demo data into `backend`.

## Notes

- The seed is additive right now. Running it again will create more demo orders and products.
- The script is intended for Shopify dev stores, not production stores.
