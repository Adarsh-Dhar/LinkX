import { NextResponse } from "next/server";

// This is the Next.js API Route that the frontend calls.
// It acts as a proxy to the Python Agent.
export async function POST(req: Request) {
  try {
    const { message } = await req.json();

    // 1. Forward the message to the Python Agent API
    // We assume the Python agent is running on port 8000
    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error(`Agent Server Error: ${response.statusText}`);
    }

    const data = await response.json();

    // 2. Return the Agent's reply to the frontend UI
    return NextResponse.json({ 
      response: data.reply 
    });

  } catch (error) {
    console.error("Chat Proxy Error:", error);
    
    // Fallback response if Python server is down
    return NextResponse.json({ 
      response: "⚠️ Error: Could not connect to the Alpha Agent (Python). Is 'agent/api.py' running?" 
    }, { status: 500 });
  }
}