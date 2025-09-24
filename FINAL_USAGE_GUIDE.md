# Final Usage Guide - Person + Feet Detection

## ✅ **Cleaned Up and Simplified!**

I've removed all the unreliable direct feet detection and kept only the **reliable person + feet detection approach** for both test and server.

## 📁 **Files You Need:**

### **Core Files:**
- `robust_calibrate.py` - Calibration with quality validation
- `robust_mapping.py` - Robust mapping with boundary constraints
- `robust_visualize.py` - Visualization functions
- `test_person_feet_detection.py` - **Test script (single player)**
- `robust_server.py` - **Main server (multiplayer)**
- `test_client.py` - Client for testing server

### **Configuration:**
- `config.yaml` - Configuration file
- `homography.npy` - Saved calibration (created after calibration)
- `grid_config.json` - Grid configuration (created after calibration)

## 🚀 **How to Use:**

### **Step 1: Calibrate the System**
```bash
python robust_calibrate.py --save --quality-threshold 0.8
```
- Place your 4 ArUco markers in corners
- Wait for quality to reach 0.8+ (shown in status)
- Press 'c' to capture when ready
- Press 'q' to quit and save

### **Step 2: Test Single Player**
```bash
python test_person_feet_detection.py
```
**Features:**
- ✅ Person detection first, then feet detection
- ✅ Grid alignment within ArUco markers
- ✅ Lava collision detection
- ✅ "PERSON X STEPPED INTO LAVA!" message
- ✅ Press **SPACE** to restart after collision
- ✅ Press **'l'** to toggle lava tiles

### **Step 3: Run Multiplayer Server**
```bash
# Terminal 1: Start server
python robust_server.py

# Terminal 2: Start client
python test_client.py
```
**Features:**
- ✅ Person detection first, then feet detection
- ✅ Multiplayer support
- ✅ WebSocket communication
- ✅ Same collision detection and restart logic

## 🎮 **Game Controls:**

| Key | Action |
|-----|--------|
| **SPACE** | Restart game after lava collision |
| **'l'** | Toggle lava tiles between corners |
| **'s'** | Save test image (test only) |
| **'q'** | Quit |

## 🎯 **What You'll See:**

- ✅ **Green grid lines** - Properly aligned within ArUco markers
- ✅ **Red lava tiles** - Areas that are "lava"
- ✅ **Colored circles** - Detected feet (yellow for left, magenta for right)
- ✅ **Person IDs** - Shows which person each foot belongs to
- ✅ **Collision messages** - "PERSON X STEPPED INTO LAVA!" when stepping on red tiles
- ✅ **Game status** - Shows if game is active or paused

## 🔧 **Camera Setup (CRITICAL!):**

**Position your camera to see FEET, not face:**
- **Height**: 1-2 feet above the ground
- **Angle**: Pointing DOWN at the floor
- **Distance**: 3-6 feet from the play area
- **Coverage**: Should see the entire ArUco marker area

## 🎯 **Expected Results:**

1. **Grid alignment** - Perfect! Grids appear only within ArUco marker boundaries
2. **Person detection** - Detects people in the camera view
3. **Feet detection** - Shows colored circles around detected feet
4. **Collision detection** - Shows "STEPPED INTO LAVA!" when stepping on red tiles
5. **Game restart** - Press SPACE to restart after collision

## 🔍 **Troubleshooting:**

### **"No persons detected"**
- Check camera position (should see people, not just floor)
- Ensure good lighting
- Make sure people are clearly visible in camera view

### **"No feet detected"**
- Check that person detection is working first
- Ensure feet are clearly visible in camera view
- Check that pose estimation is working

### **"Collision not detected"**
- Make sure you're stepping on red (lava) tiles
- Check that grid alignment is correct
- Ensure feet are being detected properly

## 💡 **Pro Tips:**

1. **Use the test script first** - `test_person_feet_detection.py` for single player testing
2. **Use the server for multiplayer** - `robust_server.py` + `test_client.py`
3. **Position camera correctly** - This is the most important factor
4. **Test with different people** - Make sure detection works for different people
5. **Use good lighting** - Shadows can break detection
6. **Keep ArUco markers clean** - Dirty or wrinkled markers don't work well

## 🎮 **Game Flow:**

1. **Calibrate** - Run calibration to set up the grid
2. **Test** - Run test script to verify everything works
3. **Play** - Step into red areas to trigger lava collision
4. **Restart** - Press SPACE to restart after collision
5. **Multiplayer** - Use server + client for multiple players

This approach is **much more reliable** than direct feet detection and will work consistently for your "Floor is Lava" game! 🎯🔥

