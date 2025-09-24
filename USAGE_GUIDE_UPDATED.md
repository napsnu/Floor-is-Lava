# Updated Usage Guide - Two Detection Approaches

## 🎯 **Two Different Approaches Created:**

### 1. **Direct Feet Detection** (Single Player)
- **File**: `test_direct_feet_detection.py`
- **Method**: Detects feet directly using computer vision
- **Best for**: Single player testing, simpler setup
- **No person detection needed**

### 2. **Person + Feet Detection** (Multiplayer)
- **File**: `robust_server_updated.py`
- **Method**: Detects persons first, then their feet
- **Best for**: Multiplayer scenarios, better tracking
- **Tracks which feet belong to which person**

## 🚀 **How to Use Each Approach:**

### **Approach 1: Direct Feet Detection (Single Player)**

```bash
# 1. First, calibrate the system
python robust_calibrate.py --save --quality-threshold 0.8

# 2. Run the direct feet detection test
python test_direct_feet_detection.py
```

**Features:**
- ✅ Direct feet detection (no person detection)
- ✅ Lava collision detection
- ✅ "STEPPED INTO LAVA!" message
- ✅ Press **SPACE** to restart after collision
- ✅ Press **'l'** to toggle lava tiles
- ✅ Press **'q'** to quit

**What you'll see:**
- Green grid lines within ArUco markers
- Red lava tiles
- Yellow bounding boxes around detected feet
- Collision messages in console and on screen

### **Approach 2: Person + Feet Detection (Multiplayer)**

```bash
# 1. First, calibrate the system
python robust_calibrate.py --save --quality-threshold 0.8

# 2. Run the updated server
python robust_server_updated.py

# 3. In another terminal, run the test client
python test_client.py
```

**Features:**
- ✅ Person detection first
- ✅ Feet detection per person
- ✅ Multiplayer support
- ✅ WebSocket communication
- ✅ Press **SPACE** to restart after collision
- ✅ Press **'r'** to restart game
- ✅ Press **'l'** to toggle lava tiles

## 🎮 **Game Controls:**

### **Direct Feet Detection Test:**
- **SPACE** - Restart game after collision
- **'l'** - Toggle lava tiles between corners
- **'s'** - Save test image
- **'q'** - Quit

### **Server + Client:**
- **SPACE** - Restart game after collision
- **'r'** - Restart game (same as space)
- **'l'** - Toggle lava tiles
- **'q'** - Quit client

## 🔧 **Camera Setup (CRITICAL!):**

**Position your camera to see FEET, not face:**
- **Height**: 1-2 feet above the ground
- **Angle**: Pointing DOWN at the floor
- **Distance**: 3-6 feet from the play area
- **Coverage**: Should see the entire ArUco marker area

## 📊 **Comparison Table:**

| Feature | Direct Feet Detection | Person + Feet Detection |
|---------|----------------------|------------------------|
| **Complexity** | Simple | More complex |
| **Players** | Single player | Multiplayer |
| **Accuracy** | Good for single player | Better for multiple people |
| **Setup** | Easy | Requires server + client |
| **Real-time** | Yes | Yes (via WebSocket) |
| **Collision Detection** | ✅ Yes | ✅ Yes |
| **Game Restart** | ✅ Space key | ✅ Space key |
| **Lava Toggle** | ✅ 'l' key | ✅ 'l' key |

## 🎯 **Recommended Testing Sequence:**

### **For Single Player Testing:**
1. **Calibrate**: `python robust_calibrate.py --save --quality-threshold 0.8`
2. **Test**: `python test_direct_feet_detection.py`
3. **Position camera** to see your feet
4. **Step into red areas** - you should see collision messages
5. **Press SPACE** to restart after collision

### **For Multiplayer Testing:**
1. **Calibrate**: `python robust_calibrate.py --save --quality-threshold 0.8`
2. **Start server**: `python robust_server_updated.py`
3. **Start client**: `python test_client.py` (in another terminal)
4. **Position camera** to see all players' feet
5. **Step into red areas** - you should see collision messages
6. **Press SPACE** to restart after collision

## 🔍 **Troubleshooting:**

### **"No feet detected"**
- Check camera position (should see feet, not face)
- Ensure good lighting
- Wear contrasting shoes (dark shoes on light floor)
- Try adjusting the detection parameters in the code

### **"Collision not detected"**
- Make sure you're stepping on red (lava) tiles
- Check that grid alignment is correct
- Ensure feet are clearly visible in camera view

### **"Game not restarting"**
- Press SPACE key (not Enter)
- Make sure the game window is focused
- Check console for restart messages

## 💡 **Pro Tips:**

1. **Use the direct feet detection** for quick testing and single player
2. **Use the person + feet detection** for multiplayer and production
3. **Position camera correctly** - this is the most important factor
4. **Test with different shoe colors** to see what works best
5. **Use good lighting** - shadows can break detection
6. **Keep ArUco markers clean** and flat

## 🎮 **Expected Results:**

- ✅ Grid lines appear ONLY within ArUco marker boundaries
- ✅ Red lava tiles are clearly visible
- ✅ Feet are detected and shown with bounding boxes
- ✅ "STEPPED INTO LAVA!" message appears when stepping on red tiles
- ✅ Game restarts when you press SPACE
- ✅ Lava tiles can be toggled with 'l' key

Both approaches should work perfectly for your "Floor is Lava" game! 🎯🔥
