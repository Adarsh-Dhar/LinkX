
import { prisma } from "@/lib/db";
import { notFound } from "next/navigation";
import RatingsChart from "@/components/market/ratings-chart";

export default async function NodeDetailsPage({ params }: { params: { id: string } }) {
	const node = await prisma.alphaNode.findUnique({
		where: { id: params.id },
		include: {
			dataLogs: {
				orderBy: { fetchedAt: 'desc' },
				take: 50,
			},
		},
	});

	if (!node) notFound();

	return (
		<div className="p-6 space-y-8">
			<header>
				<h1 className="text-3xl font-bold">{node.title}</h1>
				<p className="text-muted-foreground">{node.description}</p>
				<div className="mt-2 badge">{node.more_context}</div>
			</header>

			{/* Ratings History Graph */}
			<section className="bg-card p-4 rounded-lg border">
				<h2 className="text-xl font-semibold mb-4">Ratings Over Time</h2>
				<RatingsChart nodeId={node.id} />
			</section>

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
