import { NextResponse } from "next/server";
import { broadcastEvent } from "../events/route";

export async function POST(req: Request) {
  try {
    const status = await req.json();
    broadcastEvent({ type: "trade_status", ...status });
    return NextResponse.json({ ok: true });
  } catch (error) {
    return NextResponse.json({ error: "Failed to broadcast trade status" }, { status: 500 });
  }
}
