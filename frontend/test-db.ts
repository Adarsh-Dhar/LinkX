import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function test() {
  console.log('📋 Testing database connection...')
  
  try {
    const count = await prisma.alphaNode.count()
    console.log(`✅ Database connected. Nodes in DB: ${count}`)
    
    const nodes = await prisma.alphaNode.findMany({ select: { name: true, price: true, port: true } })
    console.log('📊 Nodes:')
    nodes.forEach(n => console.log(`  - ${n.name} ($${n.price} USDC, Port ${n.port})`))
  } catch (e) {
    console.error('❌ Error:', e)
  } finally {
    await prisma.$disconnect()
  }
}

test()
