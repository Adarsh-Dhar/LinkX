#!/usr/bin/env node
// populate_nodes.js - Directly populate nodes into the database

const fs = require('fs');
const path = require('path');

// Load .env manually
const envPath = path.join(__dirname, '.env');
const envContent = fs.readFileSync(envPath, 'utf8');
envContent.split('\n').forEach(line => {
  if (line.trim() && !line.startsWith('#')) {
    const [key, ...valueParts] = line.split('=');
    const value = valueParts.join('=').trim();
    process.env[key.trim()] = value;
  }
});

// Force the correct database URL
process.env.DATABASE_URL = 'file:/Users/adarsh/Documents/alpha-consumer/agent/agent_state.db';

const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

const NODES = [
  {
    name: 'Market Microstructure & Execution',
    title: 'Market Microstructure & Execution',
    url: 'http://localhost:4001/api/microstructure',
    nodeType: 'microstructure',
    category: 'market',
    port: 4001,
    description: 'Monitors order flow imbalances, market depth anomalies, and optimal execution paths. Detects frontrunning and MEV patterns.',
    qualityScore: 88,
    price: 0.25,
  },
  {
    name: 'Alternative Intelligence & Sentiment',
    title: 'Alternative Intelligence & Sentiment',
    url: 'http://localhost:4002/api/sentiment',
    nodeType: 'sentiment',
    category: 'sentiment',
    port: 4002,
    description: 'Real-time sentiment analysis from social media, news outlets, and on-chain whale wallets. Capturing collective psychology.',
    qualityScore: 85,
    price: 0.35,
  },
  {
    name: 'Supply Chain & Global Macro',
    title: 'Supply Chain & Global Macro',
    url: 'http://localhost:4003/api/macro',
    nodeType: 'macro',
    category: 'macro',
    port: 4003,
    description: 'Monitors large-scale economic and physical world data that impacts long-term asset valuations.',
    qualityScore: 92,
    price: 0.65,
  },
];

async function populateNodes() {
  console.log('🚀 Starting node population...');
  
  for (const node of NODES) {
    try {
            const created = await prisma.alphaNode.create({
              data: {
                title: node.title,
                nodeType: node.nodeType,
                category: node.category,
                endpointUrl: node.url,
                description: node.description,
                price: node.price,
                latencyMs: 0,
                status: 'active',
                lastUpdated: new Date(),
                icon: 'activity',
                isPurchased: false,
                whitelisted: false,
                // Optional fields matching schema
                granularity: undefined,
                historicalWinRate: 0.0,
                more_context: undefined,
                ratings: 0,
                lastPurchaseTime: undefined,
              },
            });
      console.log(`✅ Created node: ${node.name} (Quality: ${node.qualityScore}, Price: $${node.price})`);
    } catch (err) {
      console.error(`❌ Error creating node ${node.name}:`, err.message);
    }
  }
  
  // Fetch all nodes to verify
  const allNodes = await prisma.alphaNode.findMany();
  console.log(`\n📊 Database now contains ${allNodes.length} nodes:`);
  allNodes.forEach((n) => {
    console.log(`   - ${n.name} (${n.nodeType}): Quality=${n.qualityScore}, Price=$${n.price}`);
  });
  
  await prisma.$disconnect();
  console.log('\n✅ Node population complete!');
}

populateNodes().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
