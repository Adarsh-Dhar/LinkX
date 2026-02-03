/*
  Warnings:

  - You are about to drop the `AlphaSignal` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropTable
PRAGMA foreign_keys=off;
DROP TABLE "AlphaSignal";
PRAGMA foreign_keys=on;

-- CreateTable
CREATE TABLE "AlphaNode" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "description" TEXT,
    "price" REAL NOT NULL DEFAULT 0.0,
    "reputation" INTEGER NOT NULL DEFAULT 0,
    "status" TEXT NOT NULL DEFAULT 'active',
    "isPurchased" BOOLEAN NOT NULL DEFAULT false,
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

-- CreateTable
CREATE TABLE "_TradeAlphaNodes" (
    "A" TEXT NOT NULL,
    "B" TEXT NOT NULL,
    CONSTRAINT "_TradeAlphaNodes_A_fkey" FOREIGN KEY ("A") REFERENCES "AlphaNode" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "_TradeAlphaNodes_B_fkey" FOREIGN KEY ("B") REFERENCES "Trade" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "_TradeAlphaNodes_AB_unique" ON "_TradeAlphaNodes"("A", "B");

-- CreateIndex
CREATE INDEX "_TradeAlphaNodes_B_index" ON "_TradeAlphaNodes"("B");
