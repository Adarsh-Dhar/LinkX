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

-- CreateIndex
CREATE UNIQUE INDEX "Trade_txHash_key" ON "Trade"("txHash");
