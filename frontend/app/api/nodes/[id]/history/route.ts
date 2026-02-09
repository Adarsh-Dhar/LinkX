import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(request: Request, { params }: { params: { id: string } }) {
  // Optionally support ?range=24h, 7d, etc.
  const nodeId = params.id;
  const logs = await prisma.dataLog.findMany({
    where: { nodeId },
    orderBy: { fetchedAt: "desc" },
    take: 50,
    select: {
      fetchedAt: true,
      normalized: true,
    },
  });

  // Format for chart
  const chartData = logs.map((log: { fetchedAt: Date; normalized: number | null }) => ({
    time: log.fetchedAt,
    rating: log.normalized,
  }));

  return NextResponse.json(chartData);
}
