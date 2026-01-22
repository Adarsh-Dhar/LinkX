import { PrismaClient } from '@prisma/client'

// Initialize Prisma Client
const prisma = new PrismaClient()

const CATEGORIES = ["Sentiment", "On-Chain", "Technical", "Whale Watch", "News AI", "Macro"];
const ADJECTIVES = ["Quantum", "Hyper", "Neural", "Deep", "Global", "Fast", "Smart", "Alpha", "Omega", "Prime"];
const NOUNS = ["Scanner", "Oracle", "Vision", "Flow", "Pulse", "Signal", "Metric", "Index", "Radar", "Sentience"];

function getRandomInt(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function getRandomFloat(min: number, max: number) {
  return parseFloat((Math.random() * (max - min) + min).toFixed(2));
}

async function main() {
  console.log('🌱 Seeding Alpha Market Nodes...');

  // 1. Clear existing nodes to avoid duplicates
  await prisma.alphaNode.deleteMany();

  const nodes = [];

  // 2. Generate 48 Unique Nodes
  for (let i = 0; i < 48; i++) {
    const category = CATEGORIES[i % CATEGORIES.length];
    const adj = ADJECTIVES[Math.floor(Math.random() * ADJECTIVES.length)];
    const noun = NOUNS[Math.floor(Math.random() * NOUNS.length)];
    const name = `${adj} ${noun} ${getRandomInt(1, 9)}00`; // e.g. "Quantum Scanner 300"

    nodes.push({
      name: name,
      category: category,
      description: `Real-time ${category.toLowerCase()} data feed powered by ${getRandomInt(3, 10)} sub-nodes. Optimized for Cronos chain.`,
      price: getRandomFloat(15.00, 450.00), // Random Price between $15 and $450
      reputation: getRandomInt(65, 99),     // Random Score
      status: Math.random() > 0.1 ? "active" : "offline", // 90% chance active
      isPurchased: Math.random() > 0.8,     // 20% chance already owned
      icon: ["activity", "zap", "bar-chart", "globe"][Math.floor(Math.random() * 4)]
    });
  }

  // 3. Insert into DB
  for (const node of nodes) {
    await prisma.alphaNode.create({ data: node });
  }

  console.log(`✅ Created 48 Market Nodes.`);
}

main()
  .then(async () => {
    await prisma.$disconnect()
  })
  .catch(async (e) => {
    console.error(e)
    await prisma.$disconnect()
    process.exit(1)
  })
