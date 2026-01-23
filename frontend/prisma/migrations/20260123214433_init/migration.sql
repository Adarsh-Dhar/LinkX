-- CreateTable
CREATE TABLE "Trade" (
    "id" TEXT NOT NULL,
    "tokenIn" TEXT NOT NULL,
    "tokenOut" TEXT NOT NULL,
    "amountIn" DOUBLE PRECISION NOT NULL,
    "amountOut" DOUBLE PRECISION NOT NULL,
    "priceInUsd" DOUBLE PRECISION NOT NULL,
    "priceOutUsd" DOUBLE PRECISION NOT NULL,
    "valueInUsd" DOUBLE PRECISION NOT NULL,
    "valueOutUsd" DOUBLE PRECISION NOT NULL,
    "realizedPnL" DOUBLE PRECISION NOT NULL,
    "pnlPercentage" DOUBLE PRECISION NOT NULL,
    "isWin" BOOLEAN NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL,
    "strategy" TEXT,
    "reasoning" TEXT,
    "txHash" TEXT NOT NULL,
    "blockNumber" INTEGER,
    "status" TEXT NOT NULL DEFAULT 'CONFIRMED',
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Trade_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AlphaSignal" (
    "id" TEXT NOT NULL,
    "source" TEXT NOT NULL,
    "rawSignal" TEXT NOT NULL,
    "costUsd" DOUBLE PRECISION NOT NULL,
    "executed" BOOLEAN NOT NULL DEFAULT false,
    "tradeId" TEXT,
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AlphaSignal_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PortfolioSnapshot" (
    "id" TEXT NOT NULL,
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "totalValueUsd" DOUBLE PRECISION NOT NULL,
    "croBalance" DOUBLE PRECISION NOT NULL,
    "usdcBalance" DOUBLE PRECISION NOT NULL,
    "otherBalance" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "alphaCount" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "PortfolioSnapshot_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SystemState" (
    "key" TEXT NOT NULL,
    "value" TEXT NOT NULL,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "SystemState_pkey" PRIMARY KEY ("key")
);

-- CreateTable
CREATE TABLE "AlphaNode" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "price" DOUBLE PRECISION NOT NULL,
    "reputation" INTEGER NOT NULL,
    "icon" TEXT NOT NULL DEFAULT 'activity',
    "status" TEXT NOT NULL DEFAULT 'active',
    "isPurchased" BOOLEAN NOT NULL DEFAULT false,
    "endpointUrl" TEXT,
    "apiKey" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AlphaNode_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DataLog" (
    "id" TEXT NOT NULL,
    "nodeId" TEXT NOT NULL,
    "data" TEXT NOT NULL,
    "normalized" DOUBLE PRECISION,
    "fetchedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "DataLog_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TradeDecision" (
    "id" TEXT NOT NULL,
    "tradeId" TEXT NOT NULL,
    "dataLogId" TEXT NOT NULL,
    "decidedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "TradeDecision_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Trade_txHash_key" ON "Trade"("txHash");

-- AddForeignKey
ALTER TABLE "AlphaSignal" ADD CONSTRAINT "AlphaSignal_tradeId_fkey" FOREIGN KEY ("tradeId") REFERENCES "Trade"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DataLog" ADD CONSTRAINT "DataLog_nodeId_fkey" FOREIGN KEY ("nodeId") REFERENCES "AlphaNode"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TradeDecision" ADD CONSTRAINT "TradeDecision_tradeId_fkey" FOREIGN KEY ("tradeId") REFERENCES "Trade"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TradeDecision" ADD CONSTRAINT "TradeDecision_dataLogId_fkey" FOREIGN KEY ("dataLogId") REFERENCES "DataLog"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
