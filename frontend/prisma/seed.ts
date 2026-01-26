import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  console.log('🌱 Starting seed...')

  // Optional: Clear existing nodes to avoid duplicates during testing
  await prisma.alphaNode.deleteMany()

  const nodes = [
    {
      name: 'Market Microstructure & Execution',
      category: 'Technical',
      description: 'Level 2/3 Order Book Depth, Tick-by-Tick Data, and Volume Velocity.',
      price: 0.25,
      reputation: 98,
      status: 'active',
      isPurchased: false,
      endpointUrl: 'http://localhost:4001/api/microstructure',
      apiKey: null,
      icon: 'activity',
      qualityScore: 98,
      latencyMs: 5,
      assetCoverage: 'WETH, USDC',
      granularity: 'Tick',
      hasPitFlag: true
    },
    {
      name: 'Alternative Intelligence & Sentiment',
      category: 'Sentiment',
      description: 'NLP Social Sentiment, Satellite Geospatial monitoring, and Digital Footprints.',
      price: 0.45,
      reputation: 88,
      status: 'active',
      isPurchased: false,
      endpointUrl: 'http://localhost:4002/api/sentiment',
      apiKey: null,
      icon: 'zap',
      qualityScore: 85,
      latencyMs: 150,
      assetCoverage: 'WETH, USDC',
      granularity: '1m',
      hasPitFlag: true
    },
    {
      name: 'Supply Chain & Global Macro',
      category: 'News',
      description: 'Shipping Activity (AIS), Energy Infrastructure Alerts, and Global ECO indicators.',
      price: 0.65,
      reputation: 92,
      status: 'active',
      isPurchased: false,
      endpointUrl: 'http://localhost:4003/api/macro',
      apiKey: null,
      icon: 'globe',
      qualityScore: 92,
      latencyMs: 500,
      assetCoverage: 'Global',
      granularity: 'Daily',
      hasPitFlag: true
    }
  ]

  for (const node of nodes) {
    const createdNode = await prisma.alphaNode.create({
      data: node,
    })
    console.log(`✅ Created node: ${createdNode.name}`)
  }

  console.log('🚀 Seeding finished.')
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })