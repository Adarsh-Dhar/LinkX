/*
  Warnings:

  - You are about to drop the `AlphaNode` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the column `nodeId` on the `DataLog` table. All the data in the column will be lost.

*/
-- DropTable
PRAGMA foreign_keys=off;
DROP TABLE "AlphaNode";
PRAGMA foreign_keys=on;

-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_DataLog" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "data" TEXT NOT NULL,
    "normalized" REAL,
    "fetchedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO "new_DataLog" ("data", "fetchedAt", "id", "normalized") SELECT "data", "fetchedAt", "id", "normalized" FROM "DataLog";
DROP TABLE "DataLog";
ALTER TABLE "new_DataLog" RENAME TO "DataLog";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
