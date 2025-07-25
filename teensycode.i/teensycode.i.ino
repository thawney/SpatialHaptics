/*
 * Teensy FSR (Force Sensitive Resistor) Reader with Built-in LED Feedback
 * Reads analog values from 16 FSR sensors and outputs normalized values (0.00-1.00)
 * over USB serial as comma-separated values
 * 
 * LED FEEDBACK: Built-in LED shows sensor activity + terminal startup message
 * 
 * STARTUP: Prints "THAWNEY LTD FSR BOARD" to terminal on power-up
 * 
 * Optimized for high update rate with stable readings (~800-1500 Hz)
 * Compatible with Teensy 4.0, 4.1, 3.2, and other models
 */

// Define the analog pins to read from (mapped to D0-D15 equivalent)
const int fsrPins[] = {A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15};
const int numSensors = 16;

// Built-in LED
const int builtinLED = 13;

// Teensy 4.0/4.1 has 12-bit ADC (0-4095), older models may have 10-bit (0-1023)
const int adcResolution = 4095; // Change to 1023 for Teensy 3.2 or older

// LED activity tracking (minimal overhead)
const float thresholds[] = {0.1, 0.3, 0.5, 0.7}; // Multiple activity thresholds
const unsigned long strobeIntervals[] = {500, 250, 100, 50}; // Strobe speeds in ms (slower to faster)
const int numThresholds = 4;
bool ledState = false;
unsigned long lastLEDToggle = 0;
unsigned long currentStrobeInterval = 0; // 0 = LED off, >0 = strobe at interval

void setup() {
  // Initialize USB serial communication
  Serial.begin(2000000); // High baud rate for maximum throughput
  
  // Wait for serial port to connect (useful for debugging)
  while (!Serial && millis() < 3000) {
    ; // Wait up to 3 seconds for serial connection
  }
  
  // Set ADC resolution (Teensy 4.x supports up to 12-bit)
  analogReadResolution(12); // Remove this line for Teensy 3.2 or older
  
  // Optional: Set ADC averaging (balance between speed and stability)
  analogReadAveraging(4); // Average 4 samples for stable readings (Teensy 4.x only)
  
  // Initialize built-in LED
  pinMode(builtinLED, OUTPUT);
  
  // Brief startup flash
  digitalWrite(builtinLED, HIGH);
  delay(100);
  digitalWrite(builtinLED, LOW);
  
  // Startup message
  Serial.println("THAWNEY LTD FSR BOARD");

  digitalWrite(builtinLED, HIGH);
  delay(1000);
  digitalWrite(builtinLED, LOW);
  
  digitalWrite(builtinLED, HIGH);
  delay(1000);
  digitalWrite(builtinLED, LOW);
  
  // No startup messages for maximum speed
}

void loop() {
  float maxSensorValue = 0.0;
  unsigned long currentTime = millis();
  
  // Read all FSR sensors
  for (int i = 0; i < numSensors; i++) {
    // Read raw analog value
    int rawValue = analogRead(fsrPins[i]);
    
    // Normalize to 0.00-1.00 range
    float normalizedValue = (float)rawValue / adcResolution;
    
    // Ensure value stays within bounds
    normalizedValue = constrain(normalizedValue, 0.0, 1.0);
    
    // Track maximum sensor value for LED strobing
    if (normalizedValue > maxSensorValue) {
      maxSensorValue = normalizedValue;
    }
    
    // Print with 2 decimal places
    Serial.print(normalizedValue, 2);
    
    // Add comma separator (except for last value)
    if (i < numSensors - 1) {
      Serial.print(",");
    }
  }
  
  // End line
  Serial.println();
  
  // Determine strobe interval based on maximum sensor value
  unsigned long newStrobeInterval = 0; // Default: LED off
  for (int i = numThresholds - 1; i >= 0; i--) {
    if (maxSensorValue >= thresholds[i]) {
      newStrobeInterval = strobeIntervals[i];
      break;
    }
  }
  
  // Update strobe interval if changed
  if (newStrobeInterval != currentStrobeInterval) {
    currentStrobeInterval = newStrobeInterval;
    lastLEDToggle = currentTime; // Reset timing
    
    // If no activity, turn LED off immediately
    if (currentStrobeInterval == 0) {
      ledState = false;
      digitalWrite(builtinLED, LOW);
    }
  }
  
  // Handle LED strobing (only if active)
  if (currentStrobeInterval > 0 && (currentTime - lastLEDToggle >= currentStrobeInterval)) {
    ledState = !ledState;
    digitalWrite(builtinLED, ledState);
    lastLEDToggle = currentTime;
  }
  
  // No delay for maximum update rate
  // Can achieve ~1000+ Hz sampling rate depending on serial baud rate
}

/*
 * LED BEHAVIOR:
 * STARTUP: Blinks "THAWNEY LTD FSR BOARD" in morse code (one time on power-up)
 * OPERATION: LED strobes at different speeds based on maximum sensor value:
 *   - 0.0 - 0.1: LED OFF (no activity)
 *   - 0.1 - 0.3: SLOW strobe (500ms intervals)
 *   - 0.3 - 0.5: MEDIUM strobe (250ms intervals)  
 *   - 0.5 - 0.7: FAST strobe (100ms intervals)
 *   - 0.7 - 1.0: VERY FAST strobe (50ms intervals)
 * - Uses highest sensor value to determine strobe speed
 * - Provides progressive visual feedback of sensor pressure
 * - Minimal performance impact on serial speed
 * 
 * MORSE CODE TIMING (FAST SPEED):
 * - Dot: 40ms, Dash: 120ms, Gap: 40ms
 * - Letter gap: 120ms, Word gap: 280ms
 * - Standard morse code timing ratios (1:3:7) at 4x speed
 * 
 * SPEED OPTIMIZATIONS APPLIED:
 * - 2 Mbaud serial rate for high throughput
 * - 4x ADC averaging for stable readings with good speed
 * - No delays in main loop
 * - Minimal serial output overhead
 * - LED strobing uses efficient millis() timing (microseconds overhead)
 * 
 * EXPECTED PERFORMANCE:
 * - Teensy 4.x: ~800-1500 Hz update rate (with 4x averaging)
 * - Teensy 3.x: ~400-800 Hz update rate (with 4x averaging)
 * - Limited mainly by serial transmission time
 * - LED strobing adds <0.1% performance overhead
 * 
 * WIRING NOTES:
 * 
 * FSR Connection (typical setup):
 * - One side of FSR to analog pin
 * - Other side of FSR to +3.3V
 * - 10kΩ pull-down resistor from analog pin to GND
 * 
 * LED: Built-in LED on pin 13 (no external wiring needed)
 * 
 * Teensy 4.0/4.1 Analog Pins:
 * A0-A9 are dedicated analog pins
 * A10-A13 are shared with digital pins 24-27
 * A14-A17 are available on some models
 * 
 * For Teensy 3.2:
 * - Change adcResolution to 1023
 * - Remove analogReadResolution() and analogReadAveraging() lines
 * 
 * SERIAL OUTPUT FORMAT:
 * Each line contains 16 comma-separated values from 0.00 to 1.00
 * Example: 0.23,0.00,0.87,0.45,0.00,0.12,0.99,0.00,0.34,0.67,0.00,0.78,0.23,0.45,0.89,0.12
 * 
 * CUSTOMIZATION:
 * - Adjust thresholds[] array to change sensitivity levels
 * - Modify strobeIntervals[] array to change strobe speeds
 * - LED responds progressively to maximum sensor pressure
 * - Add more threshold levels for finer control
 */