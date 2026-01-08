# 🚀 FINAL LAUNCH GUIDE - Alpha-Consumer System

## ✅ The "Glue" is Connected!

Your chat page now successfully dispatches the `alpha-purchased` event when the agent buys data. Here's what happens:

1. **User types:** "Buy alpha data"
2. **Agent responds:** "Alpha Purchased... AUTONOMOUS ACTION"
3. **Chat dispatches:** `alpha-purchased` event with prediction data
4. **Chart switches:** From LIVE mode to 🔮 PREDICTION MODE
5. **Result:** Purple prediction line shows future price

---

## 🎬 How to Launch the Full System

### **You need 3 separate terminals:**

#### **Terminal 1: Data Server (Backend)**
```bash
cd server
node index.js
```

**Success Check:** You should see:
```
============================================================
🚀 Data Server with Real Price Feed
============================================================
📡 Server: http://localhost:3050
```

**Test it:**
```bash
curl http://localhost:3050/market/price/CRO
```

---

#### **Terminal 2: AI Agent**
```bash
cd agent
./start_agent.sh
```

**Success Check:** You should see:
```
Agent initialized successfully
Uvicorn running on http://0.0.0.0:8000
```

---

#### **Terminal 3: Frontend UI**
```bash
cd frontend
npm run dev
```

**Success Check:** You should see:
```
✓ Ready in ... ms
Local: http://localhost:3000
```

---

## 🧪 The Final Test (3 Steps)

### **Step 1: Verify the Heartbeat**

1. Open browser: `http://localhost:3000`
2. Look at the dashboard
3. **Watch the chart:** It should update every 5 seconds
4. **Check badge:** Should show "● LIVE" (pulsing)

**✅ Success = Chart is moving/wiggling**

---

### **Step 2: Test the Alpha Feature**

1. Navigate to **Chat** page (sidebar)
2. Type: **"Buy alpha data"**
3. Press Enter

**Expected Response:**
```
Alpha Purchased... AUTONOMOUS ACTION
Payment: 0.1 USDC
Insight: [trading data]
```

---

### **Step 3: Verify Prediction Mode**

After the agent responds, watch the chart:

**✅ Expected Behavior:**
- Badge changes to: "🔮 PREDICTION MODE"
- Chart STOPS live updates
- Purple/future prediction line appears
- Console shows: "🚀 Triggering Prediction Mode..."

---

## 🎥 Demo Recording Script

### **Scene 1: The Setup (5 seconds)**
*Camera on dashboard with live chart*

**You say:**
> "This is Alpha-Consumer - an AI trading agent that pays for premium data using the x402 protocol."

---

### **Scene 2: The Live Data (10 seconds)**
*Point to the chart*

**You say:**
> "Here's the live market with REAL data from CoinGecko. The chart updates every 5 seconds."

*Wait for one update cycle - show the "● LIVE" badge*

---

### **Scene 3: The Action (15 seconds)**
*Navigate to Chat page*

**You say:**
> "Let's ask the agent to buy premium alpha data..."

*Type: "Buy alpha data"*

**You say:**
> "Watch as the agent autonomously negotiates the paywall..."

*Show the terminal logs scrolling (optional)*

---

### **Scene 4: The Payoff (10 seconds)**
*Chart switches to Prediction Mode*

**You say:**
> "And there it is! The system now shows us where the price is GOING, not just where it's been. This is the power of x402 - paying for insights that give you an edge."

*Point to the purple prediction line*

---

### **Scene 5: The Closer (5 seconds)**

**You say:**
> "Built on Cronos testnet with real payment verification. Thank you!"

*Fade out*

---

## 🐛 Troubleshooting

### Problem: Chart not updating

**Check:**
```bash
# In browser console (F12)
# Look for errors in Network tab
# Should see requests to: http://localhost:3050/market/price/CRO
```

**Fix:**
```bash
# Restart server
cd server
node index.js
```

---

### Problem: Agent not responding

**Check:**
```bash
curl http://localhost:8000/health
```

**Fix:**
```bash
cd agent
./start_agent.sh
```

---

### Problem: No prediction line

**Check browser console:**
```javascript
// You should see this after typing "Buy alpha data":
🚀 Triggering Prediction Mode...
```

**If missing:**
- Check agent response includes "Alpha Purchased"
- Verify TradingView component is listening for event

---

## 📋 Pre-Demo Checklist

Before recording:

- [ ] All 3 terminals running (server, agent, frontend)
- [ ] Chart is updating live (verify heartbeat)
- [ ] Test alpha purchase once (verify prediction works)
- [ ] Clear browser console (for clean demo)
- [ ] Close unnecessary browser tabs
- [ ] Prepare your script/talking points
- [ ] Test your microphone
- [ ] Record in good lighting

---

## 🏆 You're Ready!

**The system is complete:**
- ✅ Real data from CoinGecko
- ✅ Live chart updates every 5 seconds
- ✅ Chat dispatches alpha-purchased event
- ✅ Chart switches to Prediction Mode
- ✅ Professional UI with animations
- ✅ All components connected

**Now go record that winning demo! 🎬**

---

## 🎯 Quick Reference

**Start All:**
```bash
# Terminal 1
cd server && node index.js

# Terminal 2  
cd agent && ./start_agent.sh

# Terminal 3
cd frontend && npm run dev
```

**Test Endpoints:**
```bash
curl http://localhost:3050/market/price/CRO
curl http://localhost:3050/health
curl http://localhost:8000/health
```

**URLs:**
- Frontend: http://localhost:3000
- Server: http://localhost:3050
- Agent: http://localhost:8000

---

**Good luck! 🚀**
