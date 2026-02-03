/*
  Warnings:

  - You are about to drop the column `apiKey` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `granularity` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `hasPitFlag` on the `AlphaNode` table. All the data in the column will be lost.
  - You are about to drop the column `reputation` on the `AlphaNode` table. All the data in the column will be lost.
  - Made the column `endpointUrl` on table `AlphaNode` required. This step will fail if there are existing NULL values in that column.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_AlphaNode" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "nodeType" TEXT,
    "description" TEXT,
    "category" TEXT NOT NULL,
    "endpointUrl" TEXT NOT NULL,
    "port" INTEGER,
    "price" REAL NOT NULL DEFAULT 0.0,
    "qualityScore" INTEGER NOT NULL DEFAULT 0,
    "latencyMs" INTEGER NOT NULL DEFAULT 0,
    "assetCoverage" TEXT,
    "icon" TEXT NOT NULL DEFAULT 'activity',
    "status" TEXT NOT NULL DEFAULT 'active',
    "isPurchased" BOOLEAN NOT NULL DEFAULT false,
    "whitelisted" BOOLEAN NOT NULL DEFAULT false,
    "lastUpdated" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);
INSERT INTO "new_AlphaNode" ("assetCoverage", "category", "createdAt", "description", "endpointUrl", "icon", "id", "isPurchased", "lastUpdated", "latencyMs", "name", "price", "qualityScore", "status", "updatedAt", "whitelisted") SELECT "assetCoverage", "category", "createdAt", "description", "endpointUrl", "icon", "id", "isPurchased", "lastUpdated", "latencyMs", "name", "price", "qualityScore", "status", "updatedAt", "whitelisted" FROM "AlphaNode";
DROP TABLE "AlphaNode";
ALTER TABLE "new_AlphaNode" RENAME TO "AlphaNode";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
