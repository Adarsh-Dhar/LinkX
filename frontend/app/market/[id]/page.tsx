
import { prisma } from "@/lib/db";
import { notFound } from "next/navigation";
import RatingsChart from "@/components/market/ratings-chart";

import LogRatingClient from "./LogRatingClient";

export default async function NodeDetailsPage({ params }: { params: Promise<{ id?: string }> }) {
  const resolvedParams = await params;
  if (!resolvedParams?.id || typeof resolvedParams.id !== "string" || resolvedParams.id.trim() === "") {
    notFound();
  }

  const node = await prisma.alphaNode.findUnique({
    where: { id: resolvedParams.id },
    include: {
      dataLogs: {
        orderBy: { fetchedAt: "desc" },
        take: 50,
        include: { userRating: true },
      },
    },
  });

  if (!node) notFound();

  // Prepare ratings history for chart
  const ratings = (node.dataLogs || [])
    .map((log: any): { time: string; rating: number } | null => {
      // Only use normalized or userRating, ignore history_rating
      let rating: number | undefined = undefined;
      if (typeof log.normalized === "number") {
        rating = Math.round(log.normalized * 100);
      } else if (log.userRating && typeof log.userRating.rating === "number") {
        rating = log.userRating.rating;
      }
      if (rating === undefined) return null;
      return {
        time: new Date(log.fetchedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        rating,
      };
    })
    .filter((r: { time: string; rating: number } | null): r is { time: string; rating: number } => r !== null)
    .reverse();

  // Format fetchedAt for each log on the server
  const logsWithFormattedDate = node.dataLogs.map((log: any) => ({
    ...log,
    fetchedAtFormatted: new Date(log.fetchedAt).toISOString(), // Use ISO for consistency
  }));
  return <LogRatingClient node={{ ...node, dataLogs: logsWithFormattedDate }} ratings={ratings} />;
}
