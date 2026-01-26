// This file was moved from the project root for correct Prisma client resolution.
// Usage: pnpm tsx insert_local_alphanodes.ts

import { prisma } from "./lib/db";
console.log("[DEBUG] process.env.DATABASE_URL:", process.env.DATABASE_URL);

async function debugConnection() {
	try {
		const count = await prisma.alphaNode.count();
		console.log(`[DEBUG] AlphaNode count before insert: ${count}`);
	} catch (e) {
		console.error('[DEBUG] Error querying AlphaNode:', e);
	}
}
debugConnection();

// ...existing code from original insert_local_alphanodes.ts...
