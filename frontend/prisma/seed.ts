import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  console.log('🌱 Starting seed with demo Alpha Nodes...')

  // Optional: Clear existing nodes to avoid duplicates during testing
  await prisma.alphaNode.deleteMany()

  const nodes = [
    {
      name: 'Market Microstructure & Execution',
      nodeType: 'microstructure',
      category: 'Technical',
      description: 'This node provides deep-level insights into the immediate liquidity and trading dynamics of the WETH/USDC pair. It delivers real-time data on order book depth (bids and asks), trade velocity measured in ticks per second, and Volume Weighted Average Price (VWAP). Additionally, it monitors for advanced execution patterns like iceberg orders and provides high-precision latency metrics to ensure 98% quality-score data for high-frequency execution strategies.',
      price: 0.25,
      status: 'active',
      isPurchased: false,
      whitelisted: true,
      endpointUrl: 'http://localhost:4001/api/microstructure',
      port: 4001,
      icon: 'activity',
      qualityScore: 98,
      latencyMs: 5,
      assetCoverage: 'WETH/USDC',
      granularity: '1m',
      historicalWinRate: 0.0,
    },
    {
      name: 'Alternative Intelligence & Sentiment',
      nodeType: 'sentiment',
      category: 'Sentiment',
      description: 'This node specializes in quantifying the "human element" of the market by aggregating data from social platforms to produce a highly bullish or bearish sentiment score. It tracks social velocity changes, web traffic indices, and even simulated satellite retail occupancy data to provide a holistic view of asset demand. With an 85% quality score, it helps traders understand the psychological momentum behind price action beyond traditional chart-based technical analysis.',
      price: 0.45,
      status: 'active',
      isPurchased: false,
      whitelisted: true,
      endpointUrl: 'http://localhost:4002/api/sentiment',
      port: 4002,
      icon: 'zap',
      qualityScore: 85,
      latencyMs: 75,
      assetCoverage: 'WETH/USDC',
      granularity: '5m',
      historicalWinRate: 0.0,
    },
    {
      name: 'Supply Chain & Global Macro',
      nodeType: 'macro',
      category: 'Macro',
      description: 'This node monitors large-scale economic and physical world data that impacts long-term asset valuations. It tracks supply chain health through port congestion indices and vessel transit counts, alongside critical infrastructure metrics like energy grid stability. Furthermore, it provides high-level economic indicators, including Consumer Price Index (CPI) expectations and Central Bank biases (Hawkish vs. Dovish), maintaining a 92% quality score for fundamental research.',
      price: 0.65,
      status: 'active',
      isPurchased: false,
      whitelisted: true,
      endpointUrl: 'http://localhost:4003/api/macro',
      port: 4003,
      icon: 'globe',
      qualityScore: 92,
      latencyMs: 150,
      assetCoverage: 'Multi-asset',
      granularity: '1h',
      historicalWinRate: 0.0,
    }
  ]

  for (const node of nodes) {
    const createdNode = await prisma.alphaNode.create({
      data: node,
    })
    console.log(`✅ Created node: ${createdNode.name} (Port ${node.port}, $${node.price} USDC)`)
  }

  console.log('\n📊 Seeding finished!')
  console.log('Demo Nodes:')
  console.log('  • Microstructure (4001): $0.25 USDC, Quality: 98%, Granularity: 1m')
  console.log('  • Sentiment (4002): $0.45 USDC, Quality: 85%, Granularity: 5m')
  console.log('  • Macro (4003): $0.65 USDC, Quality: 92%, Granularity: 1h')
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })