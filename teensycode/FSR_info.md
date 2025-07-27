# FSR Sensor Technical Specifications

## Hardware

**Sensor Model:** FSR07 Force Sensitive Resistors (Ohmite)
- **Active Area:** ø14.70mm diameter
- **Overall Size:** ø18.00mm x 56.34mm length
- **Actuation Force:** <15g to reach 10MΩ
- **Force Range:** Up to 5kg
- **Response Time:** <1ms

**Microcontroller:** Teensy 4.1
- **ADC Resolution:** 12-bit (0-4095)
- **Sample Rate:** 800-1500 Hz (limited by ADC conversion + serial transmission)

**Why this range:**
- **ADC Time:** 4× averaging per sensor × 16 sensors = 64 ADC conversions per cycle
- **Serial Time:** ~50 characters per line (16 CSV values) at 2 Mbaud
- **USB Timing:** Slight variations in USB packet scheduling
- **No Fixed Timer:** Code runs continuously, actual rate varies with system load
- **Channels:** 16 sensors (pins A0-A15)

**Circuit:** Each sensor connects:
- One side to 3.3V
- Other side to analog pin + 10kΩ pull-down resistor to ground

## Data Output

**Update Rate:** 800-1500 readings per second (all 16 sensors)
**Format:** CSV line per reading: `0.23,0.87,0.45,0.12,...` (16 values)
**Range:** 0.00 to 1.00 (normalized pressure)
**Serial:** 2 Mbaud USB

## Force Mapping

| Value | Force | Description |
|-------|-------|-------------|
| 0.00 | 0g | No contact (below threshold) |
| 0.01 | 15g | Minimum detection |
| 0.50 | ~1.25kg | Moderate press |
| 1.00 | 5kg | Maximum range |

**Formula:** Estimated Force (g) ≈ Value × 5000g

## Code Operation

```cpp
// Read sensor, normalize to 0.00-1.00
int raw = analogRead(pin);
float normalized = (float)raw / 4095;
```

**LED Feedback:**
- No activity: LED off
- Light pressure (0.1-0.3): Slow blink
- Medium pressure (0.3-0.5): Medium blink  
- High pressure (0.5-1.0): Fast blink

**Performance:** <1ms latency from pressure to serial output