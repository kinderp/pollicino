#include <Arduino.h>
#include <RadioLib.h>
#include <SPI.h>

// LILYGO LoRa32 V1.6.1 / SX1276 pinout, matching the vendor reference.
static constexpr int RADIO_SCLK_PIN = 5;
static constexpr int RADIO_MISO_PIN = 19;
static constexpr int RADIO_MOSI_PIN = 27;
static constexpr int RADIO_CS_PIN = 18;
static constexpr int RADIO_DIO0_PIN = 26;
static constexpr int RADIO_RST_PIN = 23;
static constexpr int RADIO_DIO1_PIN = 33;
static constexpr int BOARD_LED = 25;

// HW-001 conservative bench profile. These are adapter settings, not
// PollicinoNet protocol constants.
static constexpr float RADIO_FREQUENCY_MHZ = 868.1f;
static constexpr float RADIO_BANDWIDTH_KHZ = 125.0f;
static constexpr uint8_t RADIO_SPREADING_FACTOR = 7;
static constexpr uint8_t RADIO_CODING_RATE = 5;  // 4/5
static constexpr uint8_t RADIO_SYNC_WORD = 0x12; // private LoRa sync word
static constexpr int8_t RADIO_POWER_DBM = 10;
static constexpr uint16_t RADIO_PREAMBLE_SYMBOLS = 8;

// SX1276 can carry larger packets, but HW-001 intentionally keeps a margin.
// PN-001 descriptors and PN-002's frozen 64-byte PNF1 frames fit comfortably.
static constexpr size_t MAX_TX_PAYLOAD = 240;
static constexpr size_t MAX_RX_PAYLOAD = 255;
static constexpr size_t SERIAL_LINE_BYTES = 512;

SX1276 radio = new Module(
    RADIO_CS_PIN,
    RADIO_DIO0_PIN,
    RADIO_RST_PIN,
    RADIO_DIO1_PIN
);

volatile bool packetReceived = false;
char serialLine[SERIAL_LINE_BYTES];
size_t serialLineLength = 0;
bool serialDiscarding = false;

void onPacketReceived() {
    packetReceived = true;
}

int8_t hexNibble(char value) {
    if (value >= '0' && value <= '9') {
        return static_cast<int8_t>(value - '0');
    }
    if (value >= 'a' && value <= 'f') {
        return static_cast<int8_t>(value - 'a' + 10);
    }
    if (value >= 'A' && value <= 'F') {
        return static_cast<int8_t>(value - 'A' + 10);
    }
    return -1;
}

bool decodeHex(const char *text, uint8_t *output, size_t capacity, size_t &outputLength) {
    const size_t length = strlen(text);
    if (length == 0 || (length % 2) != 0) {
        return false;
    }
    const size_t bytes = length / 2;
    if (bytes > capacity) {
        return false;
    }

    for (size_t index = 0; index < bytes; ++index) {
        const int8_t high = hexNibble(text[index * 2]);
        const int8_t low = hexNibble(text[index * 2 + 1]);
        if (high < 0 || low < 0) {
            return false;
        }
        output[index] = static_cast<uint8_t>((high << 4) | low);
    }
    outputLength = bytes;
    return true;
}

void printHex(const uint8_t *data, size_t length) {
    static constexpr char digits[] = "0123456789abcdef";
    for (size_t index = 0; index < length; ++index) {
        Serial.print(digits[(data[index] >> 4) & 0x0F]);
        Serial.print(digits[data[index] & 0x0F]);
    }
}

void printInfo() {
    Serial.print(F("INFO board=lilygo-lora32-v1.6.1 chip=sx1276 freq_mhz="));
    Serial.print(RADIO_FREQUENCY_MHZ, 3);
    Serial.print(F(" bw_khz="));
    Serial.print(RADIO_BANDWIDTH_KHZ, 1);
    Serial.print(F(" sf="));
    Serial.print(RADIO_SPREADING_FACTOR);
    Serial.print(F(" cr=4/"));
    Serial.print(RADIO_CODING_RATE);
    Serial.print(F(" power_dbm="));
    Serial.print(RADIO_POWER_DBM);
    Serial.print(F(" max_tx="));
    Serial.println(MAX_TX_PAYLOAD);
}

bool resumeReceive() {
    const int16_t state = radio.startReceive();
    if (state != RADIOLIB_ERR_NONE) {
        Serial.print(F("RXSTARTERR "));
        Serial.println(state);
        return false;
    }
    return true;
}

void processCommand(char *line) {
    if (strcmp(line, "PING") == 0) {
        Serial.println(F("PONG"));
        return;
    }
    if (strcmp(line, "INFO") == 0) {
        printInfo();
        return;
    }
    if (strncmp(line, "TX ", 3) != 0) {
        Serial.println(F("ERR unknown-command"));
        return;
    }

    uint8_t payload[MAX_TX_PAYLOAD];
    size_t payloadLength = 0;
    if (!decodeHex(line + 3, payload, sizeof(payload), payloadLength)) {
        Serial.println(F("ERR invalid-hex-or-length"));
        return;
    }

    // DIO0 is RxDone while listening and TxDone while transmitting. Detach the
    // receive ISR around blocking transmit so TxDone can never be mistaken for
    // an incoming packet. RadioLib exposes this action explicitly on SX127x.
    packetReceived = false;
    radio.clearPacketReceivedAction();
    radio.standby();
    const int16_t state = radio.transmit(payload, payloadLength);
    radio.setPacketReceivedAction(onPacketReceived);

    if (state == RADIOLIB_ERR_NONE) {
        digitalWrite(BOARD_LED, !digitalRead(BOARD_LED));
        Serial.print(F("TXOK "));
        Serial.println(payloadLength);
    } else {
        Serial.print(F("TXERR "));
        Serial.println(state);
    }
    resumeReceive();
}

void handleSerial() {
    while (Serial.available() > 0) {
        const char value = static_cast<char>(Serial.read());
        if (value == '\r') {
            continue;
        }
        if (value == '\n') {
            if (serialDiscarding) {
                serialDiscarding = false;
                serialLineLength = 0;
                continue;
            }

            serialLine[serialLineLength] = '\0';
            if (serialLineLength > 0) {
                processCommand(serialLine);
            }
            serialLineLength = 0;
            continue;
        }

        // Once an overlong line is detected, discard the entire remainder up
        // to newline. Never allow a tail fragment to become a fresh command.
        if (serialDiscarding) {
            continue;
        }
        if (serialLineLength + 1 >= sizeof(serialLine)) {
            serialLineLength = 0;
            serialDiscarding = true;
            Serial.println(F("ERR serial-line-too-long"));
            continue;
        }
        serialLine[serialLineLength++] = value;
    }
}

void handleReceivedPacket() {
    if (!packetReceived) {
        return;
    }
    packetReceived = false;

    const size_t length = radio.getPacketLength();
    uint8_t payload[MAX_RX_PAYLOAD];
    if (length == 0 || length > sizeof(payload)) {
        Serial.print(F("RXERR invalid-length="));
        Serial.println(length);
        resumeReceive();
        return;
    }

    const int16_t state = radio.readData(payload, length);
    if (state == RADIOLIB_ERR_NONE) {
        digitalWrite(BOARD_LED, !digitalRead(BOARD_LED));
        Serial.print(F("RX "));
        Serial.print(length);
        Serial.print(' ');
        Serial.print(radio.getRSSI(), 1);
        Serial.print(' ');
        Serial.print(radio.getSNR(), 1);
        Serial.print(' ');
        printHex(payload, length);
        Serial.println();
    } else if (state == RADIOLIB_ERR_CRC_MISMATCH) {
        Serial.println(F("RXERR crc"));
    } else {
        Serial.print(F("RXERR state="));
        Serial.println(state);
    }

    resumeReceive();
}

void setup() {
    pinMode(BOARD_LED, OUTPUT);
    digitalWrite(BOARD_LED, LOW);
    Serial.begin(115200);
    delay(200);

    SPI.begin(RADIO_SCLK_PIN, RADIO_MISO_PIN, RADIO_MOSI_PIN);

    const int16_t state = radio.begin(
        RADIO_FREQUENCY_MHZ,
        RADIO_BANDWIDTH_KHZ,
        RADIO_SPREADING_FACTOR,
        RADIO_CODING_RATE,
        RADIO_SYNC_WORD,
        RADIO_POWER_DBM,
        RADIO_PREAMBLE_SYMBOLS,
        0
    );

    if (state != RADIOLIB_ERR_NONE) {
        Serial.print(F("FATAL radio-init="));
        Serial.println(state);
        while (true) {
            delay(1000);
        }
    }

    radio.setPacketReceivedAction(onPacketReceived);
    if (!resumeReceive()) {
        while (true) {
            delay(1000);
        }
    }

    Serial.println(F("READY hw-001"));
    printInfo();
}

void loop() {
    handleReceivedPacket();
    handleSerial();
    delay(1);
}
