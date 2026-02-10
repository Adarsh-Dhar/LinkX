/*
  Warnings:

  - You are about to drop the column `port` on the `AlphaNode` table. All the data in the column will be lost.

*/
-- CreateTable
CREATE TABLE "LogRating" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "logId" TEXT NOT NULL,
    "rating" INTEGER NOT NULL,
    "comment" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "LogRating_logId_fkey" FOREIGN KEY ("logId") REFERENCES "DataLog" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_AlphaNode" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "title" TEXT NOT NULL,
    "nodeType" TEXT,
    "description" TEXT,
    "category" TEXT NOT NULL,
    "endpointUrl" TEXT NOT NULL,
    "price" REAL NOT NULL DEFAULT 0.0,
    "ratings" INTEGER NOT NULL DEFAULT 0,
    "latencyMs" INTEGER NOT NULL DEFAULT 0,
    "more_context" TEXT,
    "icon" TEXT NOT NULL DEFAULT 'activity',
    "status" TEXT NOT NULL DEFAULT 'active',
    "isPurchased" BOOLEAN NOT NULL DEFAULT false,
    "whitelisted" BOOLEAN NOT NULL DEFAULT false,
    "historicalWinRate" REAL NOT NULL DEFAULT 0.0,
    "lastPurchaseTime" DATETIME,
    "lastUpdated" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    "providerAddress" TEXT,
    "registeredAt" DATETIME,
    "registrationStatus" TEXT NOT NULL DEFAULT 'pending',
    "apiVersion" TEXT DEFAULT '1.0',
    "healthCheckUrl" TEXT,
    "lastHealthCheck" DATETIME,
    "healthStatus" TEXT NOT NULL DEFAULT 'unknown'
);
INSERT INTO "new_AlphaNode" ("apiVersion", "category", "createdAt", "description", "endpointUrl", "healthCheckUrl", "healthStatus", "historicalWinRate", "icon", "id", "isPurchased", "lastHealthCheck", "lastPurchaseTime", "lastUpdated", "latencyMs", "more_context", "nodeType", "price", "providerAddress", "ratings", "registeredAt", "registrationStatus", "status", "title", "updatedAt", "whitelisted") SELECT "apiVersion", "category", "createdAt", "description", "endpointUrl", "healthCheckUrl", "healthStatus", "historicalWinRate", "icon", "id", "isPurchased", "lastHealthCheck", "lastPurchaseTime", "lastUpdated", "latencyMs", "more_context", "nodeType", "price", "providerAddress", "ratings", "registeredAt", "registrationStatus", "status", "title", "updatedAt", "whitelisted" FROM "AlphaNode";
DROP TABLE "AlphaNode";
ALTER TABLE "new_AlphaNode" RENAME TO "AlphaNode";
CREATE UNIQUE INDEX "AlphaNode_endpointUrl_key" ON "AlphaNode"("endpointUrl");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;

-- CreateIndex
CREATE UNIQUE INDEX "LogRating_logId_key" ON "LogRating"("logId");
