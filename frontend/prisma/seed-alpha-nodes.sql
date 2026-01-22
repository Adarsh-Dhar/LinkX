INSERT INTO AlphaNode (id, name, category, description, price, reputation, icon, status, isPurchased, createdAt) VALUES
  (lower(hex(randomblob(16))), 'Quantum Scanner', 'Technical', 'Scans quantum price anomalies in real time.', 0.25, 92, 'activity', 'active', 0, CURRENT_TIMESTAMP),
  (lower(hex(randomblob(16))), 'Neural Oracle', 'Sentiment', 'Predicts market sentiment using neural networks.', 0.45, 88, 'zap', 'active', 0, CURRENT_TIMESTAMP),
  (lower(hex(randomblob(16))), 'On-Chain Watcher', 'On-Chain', 'Monitors whale and smart money movements.', 0.65, 80, 'globe', 'active', 0, CURRENT_TIMESTAMP),
  (lower(hex(randomblob(16))), 'Flash Arbitrage', 'Technical', 'Detects arbitrage opportunities across DEXs.', 0.55, 85, 'bar-chart', 'active', 0, CURRENT_TIMESTAMP),
  (lower(hex(randomblob(16))), 'Social Pulse', 'Sentiment', 'Aggregates social media signals for crypto.', 0.35, 77, 'activity', 'active', 0, CURRENT_TIMESTAMP),
  (lower(hex(randomblob(16))), 'Macro News AI', 'News', 'Summarizes macroeconomic news for traders.', 0.15, 90, 'globe', 'active', 0, CURRENT_TIMESTAMP);
