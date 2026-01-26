// Patch script: Map AlphaNode.endpointUrl to local provider endpoints
// Usage: npx tsx patch_local_endpoints.ts

import { prisma } from "./frontend/lib/db";

// These must match the order and logic in server/market_categories.js and server/registry.js
const categories = [
  "price", "volume", "spread", "depth", "mcap", "funding",
  "inflows", "outflows", "whales", "active_addr", "fees", "age",
  "social_vol", "sentiment", "search", "dominance",
  "devs", "tvl", "unlocks", "burn",
  "rsi", "ma", "volatility", "correlation"
];

const competitors = [
  { suffix: "A", type: "Premium", price: 0.2 },
  { suffix: "B", type: "Budget", price: 0.05 }
];

async function main() {
  let updates = 0;
  let port = 4000;
  for (let i = 0; i < categories.length; i++) {
    for (let j = 0; j < competitors.length; j++) {
      const cat = categories[i];
      const comp = competitors[j];
      // Compose the expected AlphaNode name
      const name = `${capitalize(cat.replace(/_/g, ' '))} (${comp.type})`;
      // Find the node by name
      const node = await prisma.alphaNode.findFirst({ where: { name } });
      if (node) {
        await prisma.alphaNode.update({
          where: { id: node.id },
          data: { endpointUrl: `http://localhost:${port}/data/payment` }
        });
        updates++;
        console.log(`✅ Patched ${name} → http://localhost:${port}/data/payment`);
      } else {
        console.warn(`⚠️  Node not found: ${name}`);
      }
      port++;
    }
  }
  console.log(`\nDone. Patched ${updates} AlphaNode endpoints.`);
  await prisma.$disconnect();
}

function capitalize(str: string) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
