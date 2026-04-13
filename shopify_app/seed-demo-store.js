import { readFileSync, existsSync } from "fs";
import { resolve } from "path";
import { demoCatalog, demoCustomers, pickRandom, randomInt } from "./demo-data.js";

function loadEnvFile() {
  const envPath = resolve(process.cwd(), ".env");
  if (!existsSync(envPath)) {
    return;
  }

  const content = readFileSync(envPath, "utf8");
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const idx = line.indexOf("=");
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    const value = line.slice(idx + 1).trim().replace(/^['"]|['"]$/g, "");
    if (!(key in process.env)) {
      process.env[key] = value;
    }
  }
}

loadEnvFile();

const shop = process.env.SHOPIFY_DEMO_STORE || process.env.SHOPIFY_SHOP;
const accessToken =
  process.env.SHOPIFY_DEMO_ACCESS_TOKEN || process.env.SHOPIFY_ADMIN_ACCESS_TOKEN;

if (!shop || !accessToken) {
  console.error(
    "Missing Shopify credentials. Set SHOPIFY_DEMO_STORE and SHOPIFY_DEMO_ACCESS_TOKEN in shopify_app/.env."
  );
  process.exit(1);
}

const apiVersion = process.env.SHOPIFY_API_VERSION || "2025-10";
const endpoint = `https://${shop}/admin/api/${apiVersion}/graphql.json`;

async function shopifyGraphQL(query, variables = {}) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Shopify-Access-Token": accessToken,
    },
    body: JSON.stringify({ query, variables }),
  });

  const data = await response.json();
  if (!response.ok || data.errors) {
    throw new Error(
      `Shopify GraphQL failed: ${JSON.stringify(data.errors || data, null, 2)}`
    );
  }
  return data.data;
}

async function createProduct(product, category) {
  const mutation = `
    mutation CreateProduct($input: ProductInput!) {
      productCreate(input: $input) {
        product {
          id
          title
          variants(first: 5) {
            nodes {
              id
              inventoryItem {
                id
              }
            }
          }
        }
        userErrors {
          field
          message
        }
      }
    }
  `;

  const input = {
    title: product.title,
    vendor: "Metly Demo",
    productType: category,
    tags: ["metly-demo", "golf", category.toLowerCase().replace(/\s+/g, "-")],
    status: "ACTIVE",
    variants: [
      {
        price: product.price,
        inventoryPolicy: "CONTINUE",
      },
    ],
  };

  const data = await shopifyGraphQL(mutation, { input });
  const result = data.productCreate;
  if (result.userErrors?.length) {
    throw new Error(JSON.stringify(result.userErrors));
  }
  return result.product;
}

async function setCostAndInventory(inventoryItemId, cost, quantity) {
  const mutation = `
    mutation UpdateInventoryItem($id: ID!, $input: InventoryItemInput!) {
      inventoryItemUpdate(id: $id, input: $input) {
        inventoryItem {
          id
        }
        userErrors {
          field
          message
        }
      }
    }
  `;

  const data = await shopifyGraphQL(mutation, {
    id: inventoryItemId,
    input: {
      cost,
      tracked: true,
    },
  });

  const errors = data.inventoryItemUpdate.userErrors;
  if (errors?.length) {
    throw new Error(JSON.stringify(errors));
  }

  const inventoryMutation = `
    mutation AdjustInventory($input: InventoryAdjustQuantitiesInput!) {
      inventoryAdjustQuantities(input: $input) {
        inventoryAdjustmentGroup {
          createdAt
        }
        userErrors {
          field
          message
        }
      }
    }
  `;

  const locationId = await getPrimaryLocationId();
  const adjustData = await shopifyGraphQL(inventoryMutation, {
    input: {
      reason: "correction",
      name: "available",
      changes: [
        {
          delta: quantity,
          inventoryItemId,
          locationId,
        },
      ],
    },
  });

  const adjustErrors = adjustData.inventoryAdjustQuantities.userErrors;
  if (adjustErrors?.length) {
    throw new Error(JSON.stringify(adjustErrors));
  }
}

let cachedLocationId = null;
async function getPrimaryLocationId() {
  if (cachedLocationId) return cachedLocationId;
  const query = `
    query {
      locations(first: 1) {
        nodes {
          id
          name
        }
      }
    }
  `;
  const data = await shopifyGraphQL(query);
  const location = data.locations.nodes[0];
  if (!location) {
    throw new Error("No Shopify location found for inventory seeding");
  }
  cachedLocationId = location.id;
  return cachedLocationId;
}

async function createCustomer(customer) {
  const mutation = `
    mutation CreateCustomer($input: CustomerInput!) {
      customerCreate(input: $input) {
        customer {
          id
          email
        }
        userErrors {
          field
          message
        }
      }
    }
  `;

  const data = await shopifyGraphQL(mutation, {
    input: {
      firstName: customer.firstName,
      lastName: customer.lastName,
      email: customer.email,
      emailMarketingConsent: {
        marketingState: "SUBSCRIBED",
        marketingOptInLevel: "SINGLE_OPT_IN",
      },
      defaultAddress: {
        address1: "Demo Allé 1",
        city: customer.city,
        zip: `${randomInt(1000, 9999)}`,
        countryCode: "DK",
      },
    },
  });

  const result = data.customerCreate;
  if (result.userErrors?.length) {
    const emailConflict = result.userErrors.some((entry) =>
      String(entry.message || "").toLowerCase().includes("email")
    );
    if (emailConflict) {
      return await findCustomerByEmail(customer.email);
    }
    throw new Error(JSON.stringify(result.userErrors));
  }

  return result.customer;
}

async function findCustomerByEmail(email) {
  const query = `
    query FindCustomer($query: String!) {
      customers(first: 1, query: $query) {
        nodes {
          id
          email
        }
      }
    }
  `;
  const data = await shopifyGraphQL(query, { query: `email:${email}` });
  return data.customers.nodes[0] || null;
}

async function createDraftOrder(customerId, variantId, quantity) {
  const mutation = `
    mutation CreateDraftOrder($input: DraftOrderInput!) {
      draftOrderCreate(input: $input) {
        draftOrder {
          id
          invoiceUrl
        }
        userErrors {
          field
          message
        }
      }
    }
  `;

  const data = await shopifyGraphQL(mutation, {
    input: {
      customerId,
      lineItems: [
        {
          variantId,
          quantity,
        },
      ],
      tags: ["metly-demo-order"],
    },
  });

  const result = data.draftOrderCreate;
  if (result.userErrors?.length) {
    throw new Error(JSON.stringify(result.userErrors));
  }
  return result.draftOrder;
}

async function completeDraftOrder(draftOrderId) {
  const mutation = `
    mutation CompleteDraftOrder($id: ID!) {
      draftOrderComplete(id: $id, paymentPending: true) {
        draftOrder {
          id
          order {
            id
            name
          }
        }
        userErrors {
          field
          message
        }
      }
    }
  `;

  const data = await shopifyGraphQL(mutation, { id: draftOrderId });
  const result = data.draftOrderComplete;
  if (result.userErrors?.length) {
    throw new Error(JSON.stringify(result.userErrors));
  }
  return result.draftOrder.order;
}

async function main() {
  console.log(`Seeding Shopify demo store: ${shop}`);

  const createdProducts = [];
  for (const categoryGroup of demoCatalog) {
    for (const product of categoryGroup.products) {
      const created = await createProduct(product, categoryGroup.category);
      const variant = created.variants.nodes[0];
      await setCostAndInventory(
        variant.inventoryItem.id,
        product.cost,
        randomInt(35, 180)
      );
      createdProducts.push({
        title: created.title,
        variantId: variant.id,
      });
      console.log(`Created product: ${created.title}`);
    }
  }

  const createdCustomers = [];
  for (const customer of demoCustomers) {
    const created = await createCustomer(customer);
    if (created) {
      createdCustomers.push(created);
      console.log(`Ready customer: ${created.email}`);
    }
  }

  let createdOrders = 0;
  for (let index = 0; index < 45; index += 1) {
    const customer = pickRandom(createdCustomers);
    const product = pickRandom(createdProducts);
    const quantity = randomInt(1, 3);
    const draftOrder = await createDraftOrder(customer.id, product.variantId, quantity);
    await completeDraftOrder(draftOrder.id);
    createdOrders += 1;
    console.log(`Created order ${createdOrders}/45 for ${customer.email}`);
  }

  console.log("");
  console.log("Demo store seed complete.");
  console.log(`Products: ${createdProducts.length}`);
  console.log(`Customers: ${createdCustomers.length}`);
  console.log(`Orders: ${createdOrders}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
