-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_AlphaNode" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "description" TEXT,
    "price" REAL NOT NULL DEFAULT 0.0,
    "reputation" INTEGER NOT NULL DEFAULT 0,
    "status" TEXT NOT NULL DEFAULT 'active',
    "isPurchased" BOOLEAN NOT NULL DEFAULT false,
    "whitelisted" BOOLEAN NOT NULL DEFAULT false,
    "endpointUrl" TEXT,
    "apiKey" TEXT,
    "icon" TEXT NOT NULL DEFAULT 'activity',
    "qualityScore" INTEGER NOT NULL DEFAULT 0,
    "latencyMs" INTEGER NOT NULL DEFAULT 0,
    "assetCoverage" TEXT,
    "granularity" TEXT,
    "lastUpdated" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "hasPitFlag" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);
INSERT INTO "new_AlphaNode" ("apiKey", "assetCoverage", "category", "createdAt", "description", "endpointUrl", "granularity", "hasPitFlag", "icon", "id", "isPurchased", "lastUpdated", "latencyMs", "name", "price", "qualityScore", "reputation", "status", "updatedAt") SELECT "apiKey", "assetCoverage", "category", "createdAt", "description", "endpointUrl", "granularity", "hasPitFlag", "icon", "id", "isPurchased", "lastUpdated", "latencyMs", "name", "price", "qualityScore", "reputation", "status", "updatedAt" FROM "AlphaNode";
DROP TABLE "AlphaNode";
ALTER TABLE "new_AlphaNode" RENAME TO "AlphaNode";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
