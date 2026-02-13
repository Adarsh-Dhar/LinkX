-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_AlphaNode" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "registrationStatus" TEXT NOT NULL DEFAULT 'pending',
    "providerAddress" TEXT,
    "apiVersion" TEXT DEFAULT '1.0',
    "registeredAt" DATETIME,
    "healthCheckUrl" TEXT,
    "lastHealthCheck" DATETIME,
    "healthStatus" TEXT NOT NULL DEFAULT 'unknown',
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
    "icon" TEXT,
    "ratings" INTEGER NOT NULL DEFAULT 0,
    "latencyMs" INTEGER,
    "assetCoverage" TEXT,
    "granularity" TEXT,
    "historicalWinRate" REAL NOT NULL DEFAULT 0.0,
    "reliabilityScore" REAL NOT NULL DEFAULT 1.0,
    "lastUpdated" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    "lastPurchaseTime" DATETIME,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO "new_AlphaNode" ("apiVersion", "assetCoverage", "category", "createdAt", "description", "endpointUrl", "granularity", "healthCheckUrl", "healthStatus", "historicalWinRate", "icon", "id", "isPurchased", "lastHealthCheck", "lastPurchaseTime", "lastUpdated", "latencyMs", "more_context", "nodeType", "price", "providerAddress", "ratings", "registeredAt", "registrationStatus", "status", "title", "updatedAt", "whitelisted") SELECT "apiVersion", "assetCoverage", "category", "createdAt", "description", "endpointUrl", "granularity", "healthCheckUrl", "healthStatus", "historicalWinRate", "icon", "id", "isPurchased", "lastHealthCheck", "lastPurchaseTime", "lastUpdated", "latencyMs", "more_context", "nodeType", "price", "providerAddress", "ratings", "registeredAt", "registrationStatus", "status", "title", "updatedAt", "whitelisted" FROM "AlphaNode";
DROP TABLE "AlphaNode";
ALTER TABLE "new_AlphaNode" RENAME TO "AlphaNode";
CREATE UNIQUE INDEX "AlphaNode_endpointUrl_key" ON "AlphaNode"("endpointUrl");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
