#include <Adafruit_Protomatter.h>
#include "image_data.h"

// Define pins (remove const!)
uint8_t rgbPins[] = {25, 26, 27, 14, 12, 13}; // R1, G1, B1, R2, G2, B2
uint8_t addrPins[] = {23, 22, 5, 17, 32};      // A, B, C, D, E
#define CLK_PIN   16
#define LAT_PIN   4
#define OE_PIN    15

#define BRIGHTNESS   170

// Create Protomatter matrix object
Adafruit_Protomatter matrix(
  64,        // Width
  4,         // Bit depth
  1,         // Number of matrix chains
  rgbPins,   // RGB pins
  4, 
  addrPins,  // Address pins
  CLK_PIN, LAT_PIN, OE_PIN, // Control pins
  false       // Double-buffering
);

// Create a buffer to store the pixel data
uint16_t screenBuffer[32][950]; // Buffer for first image
uint16_t logoBuffer[32][64]; // Buffer for first image

int scrollPos = 0;  // Scroll position tracker
bool displayFirstImage = true; // Flag to alternate between images

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Initialize matrix... 
  ProtomatterStatus status = matrix.begin(); 
  Serial.print("Protomatter begin() status: "); 
  Serial.println((int)status); 
  if(status != PROTOMATTER_OK) { 
    for(;;); 
  }
  matrix.fillScreen(0x0000);
  matrix.show();

  matrix.setTextSize(1);

  /*
  matrix.setTextWrap(true);
  matrix.setTextSize(1);
  matrix.setTextColor(matrix.color565(255, 0, 0)); // Red
  // CURSOR: setCursor(# pixels away from left side, # pixels away from top side)
  matrix.setCursor(2, 10);
  matrix.print("Fuck you");
  */
}

void loop() {
  //loadImage(trenton, 64, screenBuffer);
  //updateMatrix();
  
  int randomNumber = random(1, 11);
  if(randomNumber == 10) {
    loadImage(northeastRegionalVet, 950, screenBuffer);
  } else {
    loadImage(northeastRegional, 950, screenBuffer);
  }
  
  horizontalScroll(950, 3);

  delay(100);
  matrix.fillScreen(0x0000);
  matrix.show();

  loadImage(amtrakLogo, 64, screenBuffer);
  updateMatrix();
  
  delay(4000);
  matrix.fillScreen(0x0000);
  matrix.show();

  loadImage(bhrsRDC, 415, screenBuffer);
  horizontalScroll(415, 7);

  delay(100);
  matrix.fillScreen(0x0000);
  matrix.show();

  loadImage(bhrsLogo, 64, screenBuffer);
  updateMatrix();
  
  delay(4000);
  matrix.fillScreen(0x0000);
  matrix.show();

  loadImage(njTransit, 772, screenBuffer);
  horizontalScroll(772, 4);

  delay(100);
  matrix.fillScreen(0x0000);
  matrix.show();

  loadImage(njtLogo, 64, screenBuffer);
  updateMatrix();
  
  delay(4000);
  matrix.fillScreen(0x0000);
  matrix.show();

  loadImage(mbta, 714, screenBuffer);
  horizontalScroll(714, 4);

  delay(100);
  matrix.fillScreen(0x0000);
  matrix.show();

  loadImage(mbtaLogo, 64, screenBuffer);
  updateMatrix();
  
  delay(4000);
  matrix.fillScreen(0x0000);
  matrix.show();

  loadImage(septa, 566, screenBuffer);
  horizontalScroll(566, 4);

  delay(100);
  matrix.fillScreen(0x0000);
  matrix.show();

  loadImage(septaLogo, 64, screenBuffer);
  updateMatrix();
  
  delay(4000);
  matrix.fillScreen(0x0000);
  matrix.show();
}

void horizontalScroll(int imageWidth, int scrollSpeed) {
  for(int i = 0; i < imageWidth; i++) {
    for (int y = 0; y < 32; y++) {
      for (int x = 0; x < imageWidth; x++) {
        // Shift in both image buffers
        screenBuffer[y][x] = screenBuffer[y][x + 1]; // Shift left in first image buffer
      }
  
      // Wrap around: Move the first pixel of the row to the last column
      screenBuffer[y][imageWidth - 1] = screenBuffer[y][0];
    }
  
    // Intertwine both images during the scrolling
    updateMatrix();
  
    delay(scrollSpeed); // Adjust the speed of the scrolling
  }
}

void loadImage(const unsigned long *image, int imageWidth, uint16_t buffer[32][950]) {
  clearScreenBuffer();
  for (int y = 0; y < 32; y++) {
    for (int x = 0; x < imageWidth; x++) {
      int index = (y * imageWidth + x);
      
      uint32_t pixel = image[index];  // Assume this is a 32-bit packed value
      uint8_t r = (((pixel >> 16) & 0xFF) * BRIGHTNESS) / 255;    // Extract red (bits 16-23)
      uint8_t g = (((pixel >> 8) & 0xFF) * BRIGHTNESS) / 255;     // Extract green (bits 8-15)
      uint8_t b = (((pixel) & 0xFF) * BRIGHTNESS) / 255;            // Extract blue (bits 0-7)
      buffer[y][x] = matrix.color565(r, g, b);
    }
  }
}

void updateMatrix() {
  // Redraw the matrix based on both image buffers' data
  for (int y = 0; y < 32; y++) {
    for (int x = 0; x < 64; x++) {
      // Draw pixels from both images side-by-side
      uint16_t color = screenBuffer[y][x];
      
      // Mix or combine colors here if you want to make it more interesting, e.g., blending
      matrix.drawPixel(x, y, color);  // Draw pixel from first image
    }
  }
  matrix.show(); // Update the matrix with the new data
}

void clearScreenBuffer() {
  for (int y = 0; y < 32; y++) {
    for (int x = 0; x < 950; x++) {
      screenBuffer[y][x] = 0;
    }
  }
}
