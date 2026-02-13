-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_AlphaNode" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "registrationStatus" TEXT NOT NULL DEFAULT 'unregistered',
    "providerAddress" TEXT,
    "title" TEXT NOT NULL,
    "nodeType" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "description" TEXT,
    "more_context" TEXT,
    "price" REAL NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'active',
    "isPurchased" BOOLEAN NOT NULL DEFAULT false,
    "whitelisted" BOOLEAN NOT NULL DEFAULT false,
    "endpointUrl" TEXT NOT NULL,
    "port" INTEGER NOT NULL,
    "icon" TEXT,
    "ratings" INTEGER NOT NULL DEFAULT 0,
    "latencyMs" INTEGER,
    "assetCoverage" TEXT,
    "granularity" TEXT,
    "historicalWinRate" REAL NOT NULL DEFAULT 0.0,
    "lastUpdated" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    "lastPurchaseTime" DATETIME,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO "new_AlphaNode" ("assetCoverage", "category", "createdAt", "description", "endpointUrl", "granularity", "historicalWinRate", "icon", "id", "isPurchased", "lastPurchaseTime", "lastUpdated", "latencyMs", "more_context", "nodeType", "port", "price", "ratings", "status", "title", "updatedAt", "whitelisted") SELECT "assetCoverage", "category", "createdAt", "description", "endpointUrl", "granularity", "historicalWinRate", "icon", "id", "isPurchased", "lastPurchaseTime", "lastUpdated", "latencyMs", "more_context", "nodeType", "port", "price", "ratings", "status", "title", "updatedAt", "whitelisted" FROM "AlphaNode";
DROP TABLE "AlphaNode";
ALTER TABLE "new_AlphaNode" RENAME TO "AlphaNode";
CREATE UNIQUE INDEX "AlphaNode_endpointUrl_key" ON "AlphaNode"("endpointUrl");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
