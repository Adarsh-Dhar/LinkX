/*
  Warnings:

  - You are about to drop the column `apiVersion` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `createdAt` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `healthCheckUrl` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `healthStatus` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `lastHealthCheck` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `lastPurchaseTime` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `providerAddress` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `registeredAt` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `registrationStatus` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `updatedAt` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `normalized` on the `DataLog` table. All the data in the column will be lost.
  - Added the required column `port` to the `AlphaNode` table without a default value. This is not possible if the table is not empty.
  - Made the column `nodeType` on table `AlphaNode` required. This step will fail if there are existing NULL values in that column.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_AlphaNode" (
    "id" TEXT NOT NULL PRIMARY KEY,
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
    "lastUpdated" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO "new_AlphaNode" ("category", "description", "endpointUrl", "historicalWinRate", "icon", "id", "isPurchased", "lastUpdated", "latencyMs", "more_context", "nodeType", "price", "ratings", "status", "title", "whitelisted") SELECT "category", "description", "endpointUrl", "historicalWinRate", "icon", "id", "isPurchased", "lastUpdated", "latencyMs", "more_context", "nodeType", "price", "ratings", "status", "title", "whitelisted" FROM "AlphaNode";
DROP TABLE "AlphaNode";
ALTER TABLE "new_AlphaNode" RENAME TO "AlphaNode";
CREATE UNIQUE INDEX "AlphaNode_endpointUrl_key" ON "AlphaNode"("endpointUrl");
CREATE TABLE "new_DataLog" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "nodeId" TEXT NOT NULL,
    "data" TEXT NOT NULL,
    "fetchedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "DataLog_nodeId_fkey" FOREIGN KEY ("nodeId") REFERENCES "AlphaNode" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
INSERT INTO "new_DataLog" ("data", "fetchedAt", "id", "nodeId") SELECT "data", "fetchedAt", "id", "nodeId" FROM "DataLog";
DROP TABLE "DataLog";
ALTER TABLE "new_DataLog" RENAME TO "DataLog";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
