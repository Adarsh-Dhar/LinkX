import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Proxying the MarketAnalyst server
    const res = await fetch('http://localhost:3050/api/prices', { 
      cache: 'no-store' 
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json([], { status: 500 });
  }
}