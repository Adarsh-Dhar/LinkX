/*
  Warnings:

  - A unique constraint covering the columns `[endpointUrl]` on the table `AlphaNode` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "AlphaNode_endpointUrl_key" ON "AlphaNode"("endpointUrl");
