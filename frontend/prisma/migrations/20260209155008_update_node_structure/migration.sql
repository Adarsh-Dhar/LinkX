/*
  Warnings:

  - You are about to drop the column `assetCoverage` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `granularity` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `name` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `qualityScore` on the `AlphaNode` table. All the data in the column will be lost.
  - Added the required column `title` to the `AlphaNode` table without a default value. This is not possible if the table is not empty.
  - Added the required column `nodeId` to the `DataLog` table without a default value. This is not possible if the table is not empty.

*/
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
    "port" INTEGER,
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
INSERT INTO "new_AlphaNode" ("apiVersion", "category", "createdAt", "description", "endpointUrl", "healthCheckUrl", "healthStatus", "historicalWinRate", "icon", "id", "isPurchased", "lastHealthCheck", "lastPurchaseTime", "lastUpdated", "latencyMs", "nodeType", "port", "price", "providerAddress", "registeredAt", "registrationStatus", "status", "updatedAt", "whitelisted") SELECT "apiVersion", "category", "createdAt", "description", "endpointUrl", "healthCheckUrl", "healthStatus", "historicalWinRate", "icon", "id", "isPurchased", "lastHealthCheck", "lastPurchaseTime", "lastUpdated", "latencyMs", "nodeType", "port", "price", "providerAddress", "registeredAt", "registrationStatus", "status", "updatedAt", "whitelisted" FROM "AlphaNode";
DROP TABLE "AlphaNode";
ALTER TABLE "new_AlphaNode" RENAME TO "AlphaNode";
CREATE UNIQUE INDEX "AlphaNode_endpointUrl_key" ON "AlphaNode"("endpointUrl");
CREATE TABLE "new_DataLog" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "nodeId" TEXT NOT NULL,
    "data" TEXT NOT NULL,
    "normalized" REAL,
    "fetchedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "DataLog_nodeId_fkey" FOREIGN KEY ("nodeId") REFERENCES "AlphaNode" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_DataLog" ("data", "fetchedAt", "id", "normalized") SELECT "data", "fetchedAt", "id", "normalized" FROM "DataLog";
DROP TABLE "DataLog";
ALTER TABLE "new_DataLog" RENAME TO "DataLog";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
