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

  // 2. Deterministic, rival-style, realistic node list
  const nodePairs = [
    // Sentiment
    [
      {
        name: 'OptiSense A',
        category: 'Sentiment',
        description: 'Harnesses advanced NLP to extract optimism from the crowd. Believes in the wisdom of positive sentiment.',
        price: 120.00,
        reputation: 95,
        icon: 'activity',
      },
      {
        name: 'ContraPulse B',
        category: 'Sentiment',
        description: 'Focuses on contrarian signals, mining skepticism and fear. Sees value in negative sentiment as a warning.',
        price: 110.00,
        reputation: 91,
        icon: 'activity',
      },
    ],
    // On-Chain
    [
      {
        name: 'ChainWatch A',
        category: 'On-Chain',
        description: 'Champions transparency, tracking every on-chain move for actionable insights. Trusts in open ledgers.',
        price: 200.00,
        reputation: 97,
        icon: 'bar-chart',
      },
      {
        name: 'Anomalyze B',
        category: 'On-Chain',
        description: 'Specializes in anomaly detection, always hunting for hidden patterns and outliers. Trusts in the unexpected.',
        price: 180.00,
        reputation: 89,
        icon: 'bar-chart',
      },
    ],
    // Technical
    [
      {
        name: 'ClassicTA A',
        category: 'Technical',
        description: 'Relies on classic indicators and proven TA. Believes history repeats itself.',
        price: 150.00,
        reputation: 93,
        icon: 'zap',
      },
      {
        name: 'ChaosEdge B',
        category: 'Technical',
        description: 'Embraces experimental models and volatility. Believes in chaos and new patterns.',
        price: 140.00,
        reputation: 88,
        icon: 'zap',
      },
    ],
    // Whale Watch
    [
      {
        name: 'WhaleTrack A',
        category: 'Whale Watch',
        description: 'Monitors top wallets for smart money moves. Follows the giants.',
        price: 175.00,
        reputation: 94,
        icon: 'globe',
      },
      {
        name: 'TrapAlert B',
        category: 'Whale Watch',
        description: 'Tracks whale manipulation and market traps. Warns against blind following.',
        price: 160.00,
        reputation: 90,
        icon: 'globe',
      },
    ],
    // News AI
    [
      {
        name: 'Mainstreamer A',
        category: 'News AI',
        description: 'Aggregates mainstream news for consensus. Trusts in the collective narrative.',
        price: 100.00,
        reputation: 92,
        icon: 'activity',
      },
      {
        name: 'RumorMill B',
        category: 'News AI',
        description: 'Surfaces alternative sources and rumors. Believes in the power of the underground.',
        price: 90.00,
        reputation: 85,
        icon: 'activity',
      },
    ],
    // Macro
    [
      {
        name: 'MacroKing A',
        category: 'Macro',
        description: 'Anchors on global economic trends and fundamentals. Macro is king.',
        price: 220.00,
        reputation: 96,
        icon: 'bar-chart',
      },
      {
        name: 'MicroFocus B',
        category: 'Macro',
        description: 'Focuses on micro-events and local disruptions. Macro is noise.',
        price: 210.00,
        reputation: 90,
        icon: 'bar-chart',
      },
    ],
  ];

  // 3. Expand to 48 nodes (8 pairs per category)
  const nodes = [];
  let port = 4000;
  for (let catIdx = 0; catIdx < nodePairs.length; catIdx++) {
    for (let pairNum = 0; pairNum < 8; pairNum++) {
      const [nodeA, nodeB] = nodePairs[catIdx];
      // Slightly vary price and reputation for each instance
      nodes.push({
        ...nodeA,
        name: nodeA.name + ' #' + (pairNum + 1),
        price: nodeA.price + pairNum * 2,
        reputation: Math.max(80, nodeA.reputation - pairNum),
        status: 'active',
        isPurchased: false,
        endpointUrl: `http://localhost:${port}/data`,
        apiKey: `key-${port}`
      });
      port++;
      nodes.push({
        ...nodeB,
        name: nodeB.name + ' #' + (pairNum + 1),
        price: nodeB.price + pairNum * 2,
        reputation: Math.max(75, nodeB.reputation - pairNum),
        status: 'active',
        isPurchased: false,
        endpointUrl: `http://localhost:${port}/data`,
        apiKey: `key-${port}`
      });
      port++;
    }
  }

  // 4. Insert into DB
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
