
import { prisma } from "@/lib/db";
import { notFound } from "next/navigation";
import RatingsChart from "@/components/market/ratings-chart";



export default async function NodeDetailsPage({ params }: { params: Promise<{ id?: string }> }) {
	// Next.js 16+ dynamic route: params is a Promise
	const resolvedParams = await params;
	if (!resolvedParams?.id || typeof resolvedParams.id !== 'string' || resolvedParams.id.trim() === '') {
		notFound();
	}

	const node = await prisma.alphaNode.findUnique({
		where: { id: resolvedParams.id },
		include: {
			dataLogs: {
				orderBy: { fetchedAt: 'desc' },
				take: 50,
			},
		},
	});

	if (!node) notFound();

	// Example: ratings history from dataLogs (if available)
	// You may want to replace this with real ratings history if you store it elsewhere

	// Try to extract ratings from history_rating in log.data (JSON string), fallback to normalized
	const ratings = (node.dataLogs || [])
		.map((log: any) => {
			let rating: number | undefined = undefined;
			// Try to parse history_rating from log.data
			try {
				const parsed = typeof log.data === 'string' ? JSON.parse(log.data) : log.data;
				if (typeof parsed?.history_rating === 'number') {
					rating = parsed.history_rating;
				}
			} catch {}
			// Fallback to normalized if available
			if (rating === undefined && typeof log.normalized === 'number') {
				rating = Math.round(log.normalized * 100);
			}
			if (rating === undefined) return null;
			return {
				time: new Date(log.fetchedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
				rating,
			};
		})
		.filter((r): r is { time: string; rating: number } => r !== null)
		.reverse();

	return (
		<div className="p-6 space-y-8">
			<header>
				<h1 className="text-3xl font-bold">{node.title}</h1>
				<p className="text-muted-foreground">{node.description}</p>
				<div className="mt-2 badge">{node.more_context}</div>
			</header>

			{/* Ratings History Graph (only if data exists) */}
			{ratings.length > 0 && (
				<section className="bg-card p-4 rounded-lg border">
					<h2 className="text-xl font-semibold mb-4">Ratings Over Time</h2>
					<RatingsChart ratings={ratings} />
				</section>
			)}

			{/* Historical Data Logs */}
			<section>
				<h2 className="text-xl font-semibold mb-4">Node Data Logs</h2>
				<div className="border rounded-lg overflow-hidden">
					<table className="w-full text-sm text-left">
						<thead className="bg-muted">
							<tr>
								<th className="p-3">Timestamp</th>
								<th className="p-3">Data Point (Signal)</th>
							</tr>
						</thead>
						<tbody>
							{node.dataLogs.map((log: any) => (
								<tr key={log.id} className="border-t">
									<td className="p-3">{new Date(log.fetchedAt).toLocaleString()}</td>
									<td className="p-3 font-mono text-xs">{JSON.stringify(log.data)}</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>
			</section>
		</div>
	);
}
