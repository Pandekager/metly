#!/bin/bash
# Setup cron job for Shopify test data generation

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GENERATE_SCRIPT="$SCRIPT_DIR/src/scripts/shopify/generate_test_data.py"
CRON_ENTRY="0 0 * * * cd $SCRIPT_DIR && /Users/rasmus/.local/bin/uv run python $GENERATE_SCRIPT >> /tmp/shopify_test_data.log 2>&1"

echo "Setting up daily cron job for Shopify test data generation..."
echo ""

# Add to crontab (removes existing entry first)
crontab -l 2>/dev/null | grep -v "generate_test_data.py" | crontab -
echo "$CRON_ENTRY" | crontab -

echo "Cron job installed:"
echo "  Schedule: Daily at midnight (0 0 * * *)"
echo "  Script: $GENERATE_SCRIPT"
echo ""
echo "To view cron jobs: crontab -l"
echo "To remove: crontab -l | grep -v generate_test_data.py | crontab -"
