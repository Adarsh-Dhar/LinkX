import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

/**
 * POST /api/nodes/register
 * 
 * Registration Handshake Endpoint
 * Allows data provider nodes to self-announce to the marketplace
 * 
 * Request Body:
 * {
 *   name: string,
 *   nodeType: string,
 *   category: string,
 *   endpointUrl: string,
 *   port: number,
 *   price: number,
 *   qualityScore: number,
 *   description: string,
 *   providerAddress: string,  // Wallet that receives x402 payments
 *   assetCoverage: string,
 *   granularity: string,
 *   apiVersion?: string
 * }
 */
export async function POST(req: Request) {
  try {
    const body = await req.json();
    
    // Validate required fields
    const { name, nodeType, category, endpointUrl, port, providerAddress } = body;
    const description = body.description ?? (providerAddress ? `Pay to: ${providerAddress}` : undefined);
    
    if (!name || !endpointUrl || !port) {
      return NextResponse.json(
        { 
          error: 'Missing required fields',
          required: ['name', 'endpointUrl', 'port'],
          received: { name, endpointUrl, port }
        }, 
        { status: 400 }
      );
    }
    
    // Validate providerAddress format (Ethereum address)
    if (providerAddress && !/^0x[a-fA-F0-9]{40}$/.test(providerAddress)) {
      return NextResponse.json(
        { 
          error: 'Invalid providerAddress format',
          details: 'Must be a valid Ethereum address (0x + 40 hex chars)'
        }, 
        { status: 400 }
      );
    }
    
    // Check for port conflicts with other active nodes
    const portConflict = await prisma.alphaNode.findFirst({
      where: {
        port: body.port,
        status: 'active',
        endpointUrl: { not: endpointUrl } // Allow same node to re-register
      }
    });
    
    if (portConflict) {
      return NextResponse.json(
        { 
          error: 'Port conflict',
          details: `Port ${body.port} is already in use by node: ${portConflict.name}`,
          conflictingNode: {
            id: portConflict.id,
            name: portConflict.name,
            endpointUrl: portConflict.endpointUrl
          }
        }, 
        { status: 409 }
      );
    }
    
    // Upsert node - allow re-registration to update metadata
    const node = await prisma.alphaNode.upsert({
      where: { endpointUrl },
      update: {
        name,
        nodeType,
        category,
        port,
        price: body.price ?? 0,
        qualityScore: body.qualityScore ?? 0,
        description,
        assetCoverage: body.assetCoverage,
        granularity: body.granularity,
        providerAddress,
        apiVersion: body.apiVersion ?? '1.0',
        lastUpdated: new Date(),
        registrationStatus: 'verified',
        status: 'active'
      },
      create: {
        name,
        nodeType,
        category,
        endpointUrl,
        port,
        price: body.price ?? 0,
        qualityScore: body.qualityScore ?? 0,
        latencyMs: body.latencyMs ?? 0,
        description,
        assetCoverage: body.assetCoverage,
        granularity: body.granularity,
        providerAddress,
        apiVersion: body.apiVersion ?? '1.0',
        status: 'active',
        registrationStatus: 'verified',
        registeredAt: new Date()
      }
    });
    
    console.log(`✅ Node registered: ${node.name} (${node.id}) at ${node.endpointUrl}`);
    
    return NextResponse.json(
      { 
        success: true,
        nodeId: node.id,
        message: 'Node registered successfully',
        node: {
          id: node.id,
          name: node.name,
          endpointUrl: node.endpointUrl,
          providerAddress: node.providerAddress,
          status: node.status
        }
      }, 
      { status: 201 }
    );
    
  } catch (error: any) {
    console.error('❌ Registration error:', error);
    return NextResponse.json(
      { 
        error: 'Registration failed',
        details: error.message,
        stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
      }, 
      { status: 500 }
    );
  }
}

/**
 * GET /api/nodes/register
 * Returns registration status and requirements
 */
export async function GET() {
  return NextResponse.json({
    endpoint: '/api/nodes/register',
    method: 'POST',
    description: 'Self-registration endpoint for data provider nodes',
    requiredFields: ['name', 'endpointUrl', 'port'],
    optionalFields: [
      'nodeType', 'category', 'price', 'qualityScore', 
      'description', 'providerAddress', 'assetCoverage', 
      'granularity', 'apiVersion'
    ],
    example: {
      name: 'Example Sentiment Node',
      nodeType: 'sentiment',
      category: 'Technical',
      endpointUrl: 'http://localhost:4002/api/sentiment',
      port: 4002,
      price: 0.5,
      qualityScore: 85,
      description: 'Real-time sentiment analysis powered by AI',
      providerAddress: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
      assetCoverage: 'WXTZ/USDC',
      granularity: '1m',
      apiVersion: '1.0'
    }
  });
}
