# Camera Setup Guide for "Floor is Lava"

## 🎯 Camera Positioning is CRITICAL!

The camera needs to see your **FEET**, not your face. Here's how to set it up correctly:

### ✅ **Correct Camera Position:**
- **Height**: 1-2 feet above the ground
- **Angle**: Pointing DOWN at the floor
- **Distance**: 3-6 feet from the play area
- **Coverage**: Should see the entire ArUco marker area

### ❌ **Wrong Camera Position:**
- Camera at eye level (will see your face, not feet)
- Camera too far away (feet too small to detect)
- Camera too close (can't see full play area)
- Camera pointing horizontally (won't see floor)

## 📐 **Optimal Setup:**

```
    Camera (1-2 ft high)
         ↓ (pointing down)
    ┌─────────────────┐
    │  ArUco Markers  │
    │  ┌───┬───┐     │
    │  │ 0 │ 1 │     │  ← Your feet should be here
    │  ├───┼───┤     │
    │  │ 3 │ 2 │     │
    │  └───┴───┘     │
    └─────────────────┘
```

## 🔧 **Setup Steps:**

1. **Place ArUco markers** in a rectangle on the floor
2. **Position camera** 1-2 feet above ground, pointing down
3. **Test the view** - you should see:
   - All 4 ArUco markers clearly
   - The floor area where you'll step
   - Your feet when you step into the area

## 📱 **Camera Settings:**

### Resolution:
- **Minimum**: 640x480
- **Recommended**: 1280x720 or higher
- **Frame rate**: 30 FPS minimum

### Focus:
- **Manual focus** on the floor area
- **Auto-focus** can work but may hunt

### Lighting:
- **Even lighting** across the play area
- **No shadows** on the markers
- **Avoid backlighting** (windows behind camera)

## 🧪 **Testing Your Setup:**

Run this test to verify your camera position:

```bash
python test_with_player_detection.py
```

**What to look for:**
- ✅ Grid lines appear within ArUco markers
- ✅ You can see your feet in the camera view
- ✅ When you step into a red (lava) area, you get collision messages
- ✅ Player detection shows your feet as colored circles

## 🎮 **Game Setup:**

1. **Run calibration:**
   ```bash
   python robust_calibrate.py --save --quality-threshold 0.8
   ```

2. **Test with player detection:**
   ```bash
   python test_with_player_detection.py
   ```

3. **Run the full server:**
   ```bash
   python robust_server.py
   ```

## 🔍 **Troubleshooting:**

### "I can't see my feet"
- Lower the camera
- Point camera more downward
- Move camera closer to play area

### "Player detection not working"
- Ensure good lighting
- Wear contrasting colors (dark shoes on light floor)
- Check that feet are clearly visible in camera view

### "Grid not aligned"
- Re-run calibration with better camera position
- Ensure all 4 ArUco markers are clearly visible
- Check that markers are flat and well-lit

## 💡 **Pro Tips:**

1. **Use a tripod** or stable mount for the camera
2. **Test different heights** - 1 foot vs 2 feet can make a big difference
3. **Wear contrasting shoes** - dark shoes on light floor work best
4. **Good lighting is key** - shadows can break detection
5. **Keep markers clean** - dirty or wrinkled markers don't work well

The camera position is the most important factor for success! 🎯
