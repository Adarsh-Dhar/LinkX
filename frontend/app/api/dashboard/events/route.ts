import { NextResponse } from "next/server";

let clients: Response[] = [];

export async function GET(request: Request) {
  const { readable, writable } = new TransformStream();
  const writer = writable.getWriter();
  const encoder = new TextEncoder();

  // Write initial headers for SSE
  writer.write(encoder.encode("retry: 10000\n\n"));

  // Store client
  clients.push(writer);

  // Remove client on close
  request.signal.addEventListener("abort", () => {
    clients = clients.filter((c) => c !== writer);
    writer.close();
  });

  return new Response(readable, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}

// Helper to broadcast events to all clients
export function broadcastEvent(data: any) {
  const encoder = new TextEncoder();
  const msg = `data: ${JSON.stringify(data)}\n\n`;
  clients.forEach((writer) => writer.write(encoder.encode(msg)));
}
