/*
  Warnings:

  - You are about to drop the column `croBalance` on the `PortfolioSnapshot` table. All the data in the column will be lost.
  - Added the required column `wxtzBalance` to the `PortfolioSnapshot` table without a default value. This is not possible if the table is not empty.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_PortfolioSnapshot" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "totalValueUsd" REAL NOT NULL,
    "wxtzBalance" REAL NOT NULL,
    "usdcBalance" REAL NOT NULL,
    "otherBalance" REAL NOT NULL DEFAULT 0,
    "alphaCount" INTEGER NOT NULL DEFAULT 0
);
INSERT INTO "new_PortfolioSnapshot" ("alphaCount", "id", "otherBalance", "timestamp", "totalValueUsd", "usdcBalance") SELECT "alphaCount", "id", "otherBalance", "timestamp", "totalValueUsd", "usdcBalance" FROM "PortfolioSnapshot";
DROP TABLE "PortfolioSnapshot";
ALTER TABLE "new_PortfolioSnapshot" RENAME TO "PortfolioSnapshot";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
