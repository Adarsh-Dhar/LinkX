-- CreateTable
CREATE TABLE "Trade" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "tokenIn" TEXT NOT NULL,
    "tokenOut" TEXT NOT NULL,
    "amountIn" REAL NOT NULL,
    "amountOut" REAL NOT NULL,
    "priceInUsd" REAL NOT NULL,
    "priceOutUsd" REAL NOT NULL,
    "valueInUsd" REAL NOT NULL,
    "valueOutUsd" REAL NOT NULL,
    "realizedPnL" REAL NOT NULL,
    "pnlPercentage" REAL NOT NULL,
    "isWin" BOOLEAN NOT NULL,
    "confidence" REAL NOT NULL,
    "strategy" TEXT,
    "reasoning" TEXT,
    "txHash" TEXT NOT NULL,
    "blockNumber" INTEGER,
    "status" TEXT NOT NULL DEFAULT 'CONFIRMED',
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "AlphaSignal" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "source" TEXT NOT NULL,
    "rawSignal" TEXT NOT NULL,
    "costUsd" REAL NOT NULL,
    "executed" BOOLEAN NOT NULL DEFAULT false,
    "tradeId" TEXT,
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "AlphaSignal_tradeId_fkey" FOREIGN KEY ("tradeId") REFERENCES "Trade" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "PortfolioSnapshot" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "totalValueUsd" REAL NOT NULL,
    "croBalance" REAL NOT NULL,
    "usdcBalance" REAL NOT NULL,
    "otherBalance" REAL NOT NULL DEFAULT 0,
    "alphaCount" INTEGER NOT NULL DEFAULT 0
);

-- CreateTable
CREATE TABLE "SystemState" (
    "key" TEXT NOT NULL PRIMARY KEY,
    "value" TEXT NOT NULL,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "AlphaNode" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "price" REAL NOT NULL,
    "reputation" INTEGER NOT NULL,
    "icon" TEXT NOT NULL DEFAULT 'activity',
    "status" TEXT NOT NULL DEFAULT 'active',
    "isPurchased" BOOLEAN NOT NULL DEFAULT false,
    "endpointUrl" TEXT,
    "apiKey" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

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

-- CreateIndex
CREATE UNIQUE INDEX "Trade_txHash_key" ON "Trade"("txHash");
