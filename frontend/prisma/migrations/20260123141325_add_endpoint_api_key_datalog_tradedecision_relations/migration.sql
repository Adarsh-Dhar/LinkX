-- AlterTable
ALTER TABLE "AlphaNode" ADD COLUMN "apiKey" TEXT;
ALTER TABLE "AlphaNode" ADD COLUMN "endpointUrl" TEXT;

-- CreateTable
CREATE TABLE "DataLog" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "nodeId" TEXT NOT NULL,
    "data" TEXT NOT NULL,
    "normalized" REAL,
    "fetchedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "DataLog_nodeId_fkey" FOREIGN KEY ("nodeId") REFERENCES "AlphaNode" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "TradeDecision" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "tradeId" TEXT NOT NULL,
    "dataLogId" TEXT NOT NULL,
    "decidedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "TradeDecision_tradeId_fkey" FOREIGN KEY ("tradeId") REFERENCES "Trade" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "TradeDecision_dataLogId_fkey" FOREIGN KEY ("dataLogId") REFERENCES "DataLog" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
