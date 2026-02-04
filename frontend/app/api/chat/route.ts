import { NextResponse } from "next/server";

// Intent extraction using OpenRouter for chat-to-agent C2
async function extractIntent(message: string): Promise<{ action: string; params?: any }> {
  const systemPrompt = `You are a trading assistant that converts user speech into structured commands.
Possible actions:
- "aggressive" / "be aggressive" / "lower risk" → {"action": "SET_RISK", "risk": 0.1}
- "conservative" / "be conservative" / "higher threshold" → {"action": "SET_RISK", "risk": 0.85}
- "go long" / "buy bias" / "bullish" → {"action": "SET_BIAS", "bias": "LONG"}
- "go short" / "sell bias" / "bearish" → {"action": "SET_BIAS", "bias": "SHORT"}
- "neutral" / "no bias" / "AI discretion" → {"action": "SET_BIAS", "bias": "NONE"}
- "pause" / "stop trading" → {"action": "PAUSE"}
- "resume" / "start trading" → {"action": "RESUME"}
- anything else → {"action": "CHAT"}

Return ONLY valid JSON.`;

  try {
    const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${process.env.OPENROUTER_API_KEY}`,
      },
      body: JSON.stringify({
        model: "openai/gpt-4o-mini",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: message }
        ],
        response_format: { type: "json_object" },
        temperature: 0.2
      })
    });

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content;
    return JSON.parse(content || '{"action": "CHAT"}');
  } catch (error) {
    console.error("[Intent Extraction Error]", error);
    return { action: "CHAT" };
  }
}

// This is the Next.js API Route that the frontend calls.
// It acts as a proxy to the Python Agent.
export async function POST(req: Request) {
  try {
    const { message } = await req.json();

    // 1. Extract intent from user message
    const intent = await extractIntent(message);
    console.log("[Chat Intent]", intent);

    // 2. Route based on intent action
    if (intent.action === "SET_RISK" || intent.action === "SET_BIAS") {
      // Send override command to agent
      const overrideResponse = await fetch("http://127.0.0.1:8000/agent/control/override", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          risk: intent.action === "SET_RISK" ? intent.risk : undefined,
          bias: intent.action === "SET_BIAS" ? intent.bias : undefined
        })
      });

      const overrideData = await overrideResponse.json();
      
      if (overrideData.status === "Override Applied Successfully") {
        const config = overrideData.current_config;
        return NextResponse.json({
          response: `✅ Maneuver accepted:\n• Risk Threshold: ${config.risk_threshold}\n• Bias: ${config.forced_bias}\n• Status: ${config.paused ? "Paused" : "Active"}`
        });
      } else {
        return NextResponse.json({
          response: `⚠️ Override failed: ${overrideData.message}`
        }, { status: 400 });
      }
    }

    // 3. Otherwise, forward to chat endpoint
    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    let data;
    try {
      data = await response.json();
    } catch (e) {
      // If response is not JSON, fallback to text
      const text = await response.text();
      return NextResponse.json({
        response: `⚠️ Agent returned non-JSON response: ${text}`
      }, { status: 500 });
    }

    if (!response.ok) {
      // Forward the agent's error message if available
      return NextResponse.json({
        response: data.reply || `Agent Server Error: ${response.statusText}`
      }, { status: response.status });
    }

    // 4. Return the Agent's reply to the frontend UI
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