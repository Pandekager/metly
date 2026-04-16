# Metly Scheduled Jobs

This document describes scheduled jobs for the Metly backend.

## Test Data Generation

### Schedule

| Job Name | Cron Expression | Description |
|---------|---------------|-------------|
| Test Data Generator | `0 0 * * *` | Daily at midnight |

### Purpose

Generates Danish golf test data (products, customers, orders) in Shopify for development and testing purposes.

**Store:** Metly Test Golf

### Cron Setup

Add to crontab:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at midnight)
0 0 * * * cd /path/to/metly/backend && /usr/bin/uv run python main.py --test-data --user <USER_ID> >> /path/to/metly/backend/logs/test-data.log 2>&1
```

### Environment Variables Required

The following environment variables must be set in `.env`:

- `SHOPIFY_SHOP` - Shopify store domain (e.g., `metly-test-golf.myshopify.com`)
- `SHOPIFY_ACCESS_TOKEN` - Shopify Admin API access token
- `DB_USR_ADMIN` - Database admin username
- `DB_PWD_ADMIN` - Database admin password

### Integration

The test data generation integrates with the existing `populateDB` flow:

1. **Generate** - Creates products and orders in Shopify via `generateTestData.py`
2. **Sync** - Calls `populateDB` to sync generated data to the database

### Usage

**Standalone:**
```bash
# Generate test data only
uv run python src/scripts/generateTestData.py --products 20 --orders 10

# Dry run to preview data
uv run python src/scripts/generateTestData.py --dry-run
```

**Via main.py:**
```bash
# Generate and sync to database
uv run python main.py --test-data --user <USER_ID>
```

### Data Specifications

- **Products:** 20 default (configurable via `--products`)
- **Orders:** 10 default (configurable via `--orders`)
- **Order values:** 500-5000 DKK per order
- **Categories:** golf clubs, golf bags, golf balls, gloves, golf apparel, accessories
- **Customer data:** Danish names, addresses, cities

### Logs

Logs are written to `/path/to/metly/backend/logs/test-data.log`

Check logs for:
- Products created
- Orders created with total amounts
- Database sync status