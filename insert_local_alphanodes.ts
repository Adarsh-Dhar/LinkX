// Script to insert all 48 local provider AlphaNode records for agent_state.db
// Usage: DATABASE_URL="file:../agent/agent_state.db" npx tsx insert_local_alphanodes.ts


import { prisma } from "./lib/db";
console.log("[DEBUG] process.env.DATABASE_URL:", process.env.DATABASE_URL);
import { PrismaClient } from '@prisma/client';
const debugPrisma = new PrismaClient();
debugPrisma.$connect().then(async () => {
  const dbFile = process.env.DATABASE_URL || 'NOT SET';
  console.log("[DEBUG] Connected to DB:", dbFile);
  await debugPrisma.$disconnect();
});

const categories = [
  { id: "price", name: "Price", category: "Market Data", icon: "activity" },
  { id: "volume", name: "Volume", category: "Market Data", icon: "bar-chart" },
  { id: "spread", name: "Spread", category: "Market Data", icon: "activity" },
  { id: "depth", name: "Depth", category: "Market Data", icon: "activity" },
  { id: "mcap", name: "Mcap", category: "Market Data", icon: "bar-chart" },
  { id: "funding", name: "Funding", category: "Market Data", icon: "activity" },
  { id: "inflows", name: "Inflows", category: "On-Chain", icon: "globe" },
  { id: "outflows", name: "Outflows", category: "On-Chain", icon: "globe" },
  { id: "whales", name: "Whales", category: "On-Chain", icon: "globe" },
  { id: "active_addr", name: "Active Addr", category: "On-Chain", icon: "globe" },
  { id: "fees", name: "Fees", category: "On-Chain", icon: "globe" },
  { id: "age", name: "Age", category: "On-Chain", icon: "globe" },
  { id: "social_vol", name: "Social Vol", category: "Sentiment", icon: "activity" },
  { id: "sentiment", name: "Sentiment", category: "Sentiment", icon: "zap" },
  { id: "search", name: "Search", category: "Sentiment", icon: "activity" },
  { id: "dominance", name: "Dominance", category: "Sentiment", icon: "activity" },
  { id: "devs", name: "Devs", category: "Fundamental", icon: "bar-chart" },
  { id: "tvl", name: "Tvl", category: "Fundamental", icon: "bar-chart" },
  { id: "unlocks", name: "Unlocks", category: "Fundamental", icon: "bar-chart" },
  { id: "burn", name: "Burn", category: "Fundamental", icon: "bar-chart" },
  { id: "rsi", name: "Rsi", category: "Technical", icon: "activity" },
  { id: "ma", name: "Ma", category: "Technical", icon: "activity" },
  { id: "volatility", name: "Volatility", category: "Technical", icon: "activity" },
  { id: "correlation", name: "Correlation", category: "Technical", icon: "activity" }
];

const competitors = [
  { suffix: "A", type: "Premium", price: 0.2, reputation: 90 },
  { suffix: "B", type: "Budget", price: 0.05, reputation: 70 }
];

async function main() {
  let inserts = 0;
  let port = 4000;
  for (let i = 0; i < categories.length; i++) {
    for (let j = 0; j < competitors.length; j++) {
      const cat = categories[i];
      const comp = competitors[j];
      const name = `${cat.name} (${comp.type})`;
      const endpointUrl = `http://localhost:${port}/data/payment`;
      // Check if already exists
      const exists = await prisma.alphaNode.findFirst({ where: { name } });
      if (!exists) {
        await prisma.alphaNode.create({
          data: {
            name,
            category: cat.category,
            description: `Simulated ${cat.name} data (${comp.type})`,
            price: comp.price,
            reputation: comp.reputation,
            status: "active",
            isPurchased: false,
            icon: cat.icon,
            endpointUrl,
            apiKey: null
          }
        });
        inserts++;
        console.log(`✅ Inserted ${name}`);
      } else {
        console.log(`ℹ️  Already exists: ${name}`);
      }
      port++;
    }
  }
  console.log(`\nDone. Inserted ${inserts} new AlphaNode records.`);
  await prisma.$disconnect();
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
