#include <WiFi.h>
#include <vector>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <Adafruit_Protomatter.h>

// ===== WiFi Setup =====
const char* ssid = "Sutton Court Dojo";
const char* password = "jZYjZtmk";

// ===== Matrix Pins =====
uint8_t rgbPins[] = {25, 26, 27, 14, 12, 13}; // R1, G1, B1, R2, G2, B2
uint8_t addrPins[] = {23, 22, 5, 17, 32};      // A, B, C, D, E
#define CLK_PIN   16
#define LAT_PIN   4
#define OE_PIN    15

int brightness = 170;
// Global variable to store the raw POST body for brightness
String brightnessBody = "";
#define IMAGE_SIZE 6144

std::vector<uint8_t> imageBuffer;

// ===== Matrix Object =====
Adafruit_Protomatter matrix(
  64,        // Width
  4,         // Bit depth
  1,         // Chain
  rgbPins,
  4,
  addrPins,
  CLK_PIN, LAT_PIN, OE_PIN,
  false
);

// ===== Buffers =====
uint16_t screenBuffer[32][950]; // Buffer for wide scrolling
uint16_t logoBuffer[32][64];    // Optional secondary buffer

AsyncWebServer server(80);

void setup() {
  Serial.begin(115200);
  delay(1000);

  // ===== Connect to WiFi =====
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // ===== Matrix Init =====
  ProtomatterStatus status = matrix.begin();
  Serial.print("Protomatter begin() status: ");
  Serial.println((int)status);
  if (status != PROTOMATTER_OK) {
    while (true);
  }

  matrix.fillScreen(0x0000);
  matrix.show();

  // ===== HTTP Server =====
  server.on("/upload", HTTP_POST, [](AsyncWebServerRequest *request) {},
    NULL,
    handleUpload
  );
  
  // AsyncWebServer handler
  server.on("/set_brightness", HTTP_POST,
    [](AsyncWebServerRequest *request) {},  // onRequest left empty
    NULL,  // onUpload
    [](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
      String body = "";
      for (size_t i = 0; i < len; i++) {
        body += (char)data[i];
      }
      int newBrightness = body.toInt();
      if (newBrightness >= 0 && newBrightness <= 255) {
        brightness = newBrightness;
        Serial.printf("Brightness set to: %d\n", brightness);
        request->send(200, "text/plain", "Brightness set to " + String(brightness));
      } else {
        request->send(400, "text/plain", "Invalid brightness value");
      }
    }
  );


  server.begin();
  Serial.println("Server started");
}

void loop() {
  // No loop logic needed
}

void handleUpload(AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
  Serial.printf("Chunk received: index=%d, len=%d, total=%d\n", index, len, total);

  // First chunk? Clear the buffer
  if (index == 0) {
    imageBuffer.clear();
    imageBuffer.reserve(IMAGE_SIZE);
    Serial.println("Starting new image upload");
  }

  // Append this chunk
  imageBuffer.insert(imageBuffer.end(), data, data + len);

  // Last chunk?
  if (index + len == total) {
    Serial.printf("Upload complete. Received %d bytes\n", imageBuffer.size());

    if (imageBuffer.size() != IMAGE_SIZE) {
      Serial.println("Warning: Incomplete image data");
    }
    // Process the full image buffer
    for (int i = 0, pixel = 0; i + 2 < imageBuffer.size() && pixel < 64 * 32; i += 3, pixel++) {
      uint8_t r = imageBuffer[i];
      uint8_t g = imageBuffer[i + 1];
      uint8_t b = imageBuffer[i + 2];
      int x = pixel % 64;
      int y = pixel / 64;
      matrix.drawPixel(x, y, matrix.color565((r * brightness) / 255, (g * brightness) / 255, (b * brightness) / 255));
    }

    Serial.println("Matrix updated");
    matrix.show();

    request->send(200, "text/plain", "Image received");
  }
}

void updateMatrix() {
  for (int y = 0; y < 32; y++) {
    for (int x = 0; x < 64; x++) {
      matrix.drawPixel(x, y, screenBuffer[y][x]);
    }
  }
  matrix.show();
  Serial.println("Matrix updated.");
}

void clearScreenBuffer() {
  for (int y = 0; y < 32; y++) {
    for (int x = 0; x < 950; x++) {
      screenBuffer[y][x] = 0;
    }
  }
}
