// Metly Shopify App - Main Entry Point

import { shopifyApp } from "@shopify/shopify-api";

export const app = shopifyApp({
  apiKey: process.env.SHOPIFY_API_KEY,
  apiSecretKey: process.env.SHOPIFY_API_SECRET || "",
  appUrl: process.env.SHOPIFY_HOST || "",
  scopes:
    process.env.SHOPIFY_SCOPES?.split(",") || [
      "read_products",
      "write_products",
      "read_orders",
      "read_customers",
      "write_customers",
      "read_draft_orders",
      "write_draft_orders",
      "write_inventory",
    ],
  webhooks: {
    APP_UNINSTALLED: {
      deliveryMethod: "http",
      callbackUrl: "/webhooks/app-uninstalled",
    },
  },
  hooks: {
    afterAuth: async ({ session }) => {
      console.log("Authenticated:", session.shop);
    },
  },
  future: {
    unstable_newEmbeddedAuthStrategy: true,
  },
});

export default app;
