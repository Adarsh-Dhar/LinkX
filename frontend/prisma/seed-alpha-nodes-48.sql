-- Seed 48 AlphaNode entries with unique names, categories, and prices under $1
-- Add endpointUrl column and use real API endpoints for some nodes
INSERT INTO AlphaNode (id, name, category, description, price, reputation, icon, status, isPurchased, createdAt, endpointUrl) VALUES
(lower(hex(randomblob(16))), 'Quantum Scanner', 'Technical', 'Scans quantum price anomalies in real time.', 0.25, 92, 'activity', 'active', 0, CURRENT_TIMESTAMP, NULL),
(lower(hex(randomblob(16))), 'Neural Oracle', 'Sentiment', 'Predicts market sentiment using neural networks.', 0.45, 88, 'zap', 'active', 0, CURRENT_TIMESTAMP, 'https://api.lunarcrush.com/v2?data=assets&key=YOUR_KEY&symbol=BTC'),
(lower(hex(randomblob(16))), 'On-Chain Watcher', 'On-Chain', 'Monitors whale and smart money movements.', 0.65, 80, 'globe', 'active', 0, CURRENT_TIMESTAMP, 'https://api.covalenthq.com/v1/1/address/0x742d35Cc6634C0532925a3b844Bc454e4438f44e/transactions_v2/'),
(lower(hex(randomblob(16))), 'Flash Arbitrage', 'Technical', 'Detects arbitrage opportunities across DEXs.', 0.55, 85, 'bar-chart', 'active', 0, CURRENT_TIMESTAMP, NULL),
(lower(hex(randomblob(16))), 'Social Pulse', 'Sentiment', 'Aggregates social media signals for crypto.', 0.35, 77, 'activity', 'active', 0, CURRENT_TIMESTAMP, 'https://api.twitter.com/2/tweets/search/recent?query=bitcoin'),
(lower(hex(randomblob(16))), 'Macro News AI', 'News', 'Summarizes macroeconomic news for traders.', 0.15, 90, 'globe', 'active', 0, CURRENT_TIMESTAMP, 'https://newsapi.org/v2/top-headlines?category=business&apiKey=YOUR_KEY'),
(lower(hex(randomblob(16))), 'Chainlink Sentinel', 'On-Chain', 'Tracks Chainlink oracle updates.', 0.22, 81, 'globe', 'active', 0, CURRENT_TIMESTAMP, NULL),
(lower(hex(randomblob(16))), 'DeFi Pulse', 'Technical', 'Monitors DeFi protocol health.', 0.33, 79, 'bar-chart', 'active', 0, CURRENT_TIMESTAMP, NULL),
(lower(hex(randomblob(16))), 'Sentiment Surge', 'Sentiment', 'Detects sudden sentiment shifts.', 0.29, 83, 'zap', 'active', 0, CURRENT_TIMESTAMP, 'https://api.lunarcrush.com/v2?data=assets&key=YOUR_KEY&symbol=ETH'),
(lower(hex(randomblob(16))), 'Whale Alert', 'On-Chain', 'Alerts on large wallet movements.', 0.41, 87, 'activity', 'active', 0, CURRENT_TIMESTAMP, 'https://api.whale-alert.io/v1/transactions?api_key=YOUR_KEY'),
-- ...existing code for the rest of the nodes, set endpointUrl to NULL or real endpoints as needed
