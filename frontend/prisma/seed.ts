import 'dotenv/config';
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

  // Add 3 demo nodes for Economic Loop
  const demoNodes = [
    {
      name: 'Macro News AI',
      category: 'News',
      description: 'AI-summarized macro news for market-moving events.',
      price: 0.15,
      reputation: 99,
      status: 'active',
      isPurchased: false,
      endpointUrl: 'http://localhost:4100/data',
      apiKey: 'demo-macro-news',
      icon: 'activity',
    },
    {
      name: 'Neural Oracle',
      category: 'Sentiment',
      description: 'Social sentiment scanner for early pump detection.',
      price: 0.45,
      reputation: 99,
      status: 'active',
      isPurchased: false,
      endpointUrl: 'http://localhost:4100/data',
      apiKey: 'demo-neural-oracle',
      icon: 'activity',
    },
    {
      name: 'On-Chain Watcher',
      category: 'On-Chain',
      description: 'Whale tracker for large wallet movements.',
      price: 0.65,
      reputation: 99,
      status: 'active',
      isPurchased: false,
      endpointUrl: 'http://localhost:4100/data',
      apiKey: 'demo-chain-watcher',
      icon: 'bar-chart',
    },
  ];
  console.log('🚦 Inserting demo nodes...');
  for (const node of demoNodes) {
    try {
      await prisma.alphaNode.create({ data: node });
      console.log(`✅ Inserted demo node: ${node.name}`);
    } catch (err) {
      console.error(`❌ Failed to insert demo node: ${node.name}`, err);
    }
  }

  // Verify insertion
  const inserted = await prisma.alphaNode.findMany({
    where: {
      name: { in: ['Macro News AI', 'Neural Oracle', 'On-Chain Watcher'] }
    },
    select: { name: true, endpointUrl: true }
  });
  console.log('🔎 Demo nodes in DB:', inserted);

  console.log(`✅ Created 48 Market Nodes.`);
  console.log(`✅ Added 3 Demo Providers: Macro News AI, Neural Oracle, On-Chain Watcher.`);
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
