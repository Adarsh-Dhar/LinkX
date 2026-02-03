-- CreateTable
CREATE TABLE "AgentActivity" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "type" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "nodeId" TEXT,
    "nodePrice" REAL,
    "nodeQuality" INTEGER,
    "utilityScore" REAL,
    "alphaPerUsdcRatio" REAL,
    "signalValue" REAL,
    "signalSource" TEXT,
    "tradeBias" TEXT,
    "tradeConfidence" REAL,
    "tradeReason" TEXT,
    "riskAction" TEXT,
    "riskReason" TEXT,
    "agentThought" TEXT,
    "metadata" TEXT,
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
