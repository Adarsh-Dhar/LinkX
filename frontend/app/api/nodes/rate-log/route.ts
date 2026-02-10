import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

type LogRatingRequest = {
  logId: string;
  rating: number;
  comment?: string;
  nodeId: string;
};

/**
 * Handle creating or updating a rating for a specific data log
 * and recalculating the AlphaNode's average rating.
 */
export async function POST(req: Request) {
  try {
    const body: LogRatingRequest = await req.json();
    const { logId, rating, comment, nodeId } = body;

    // Validation: Rating must be between 1 and 10
    if (!logId || typeof rating !== "number" || rating < 1 || rating > 10 || !nodeId) {
      return NextResponse.json({ error: "Invalid logId, nodeId, or rating (1-10 required)" }, { status: 400 });
    }

    // 1. Save or Update the rating for this specific log
    await prisma.logRating.upsert({
      where: { logId },
      update: { rating, comment },
      create: { logId, rating, comment },
    });

    // 2. Fetch all ratings for logs belonging to this node
    const allRatings = await prisma.logRating.findMany({
      where: { 
        log: { nodeId: nodeId } 
      },
      select: { rating: true }
    });

    // 3. Calculate average
    const average = allRatings.length > 0
      ? allRatings.reduce((acc: number, curr: { rating: number }) => acc + curr.rating, 0) / allRatings.length
      : 0;

    // 4. Update the AlphaNode overall rating field
    await prisma.alphaNode.update({
      where: { id: nodeId },
      data: { ratings: Math.round(average) }
    });

    return NextResponse.json({ success: true, newAverage: average });
  } catch (error) {
    console.error("Rating Error:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}

/**
 * Retrieve a specific log's rating or the node's average rating
 */
export async function GET(req: Request) {
  const url = new URL(req.url);
  const logId = url.searchParams.get("logId");
  const nodeId = url.searchParams.get("nodeId");

  if (!logId && !nodeId) {
    return NextResponse.json({ error: "Missing logId or nodeId" }, { status: 400 });
  }

  let logRatingData = { rating: 0, comment: "" };
  let nodeAverage = 0;

  // Get specific log rating if requested
  if (logId) {
    const found = await prisma.logRating.findUnique({ where: { logId } });
    if (found) {
      logRatingData = { rating: found.rating, comment: found.comment || "" };
    }
  }

  // Get node average if requested
  if (nodeId) {
    const node = await prisma.alphaNode.findUnique({
      where: { id: nodeId },
      select: { ratings: true }
    });
    nodeAverage = node?.ratings || 0;
  }

  return NextResponse.json({ logRating: logRatingData, nodeAverage });
}