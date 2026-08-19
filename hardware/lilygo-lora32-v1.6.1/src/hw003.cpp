#include <Arduino.h>
#include <RadioLib.h>
#include <SPI.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <freertos/task.h>

// HW-003 keeps the HW-002T radio profile and H2 wire format frozen while
// moving asynchronous RX handling from Arduino-loop polling to a dedicated
// FreeRTOS task woken directly by the SX1276 DIO0 RX-done interrupt.

static constexpr int RADIO_SCLK_PIN = 5;
static constexpr int RADIO_MISO_PIN = 19;
static constexpr int RADIO_MOSI_PIN = 27;
static constexpr int RADIO_CS_PIN = 18;
static constexpr int RADIO_DIO0_PIN = 26;
static constexpr int RADIO_RST_PIN = 23;
static constexpr int RADIO_DIO1_PIN = 33;
static constexpr int BOARD_LED = 25;

static constexpr float RADIO_FREQUENCY_MHZ = 868.1f;
static constexpr float RADIO_BANDWIDTH_KHZ = 125.0f;
static constexpr uint8_t RADIO_SPREADING_FACTOR = 7;
static constexpr uint8_t RADIO_CODING_RATE = 5;  // 4/5
static constexpr uint8_t RADIO_SYNC_WORD = 0x12;
static constexpr int8_t RADIO_POWER_DBM = 10;
static constexpr uint16_t RADIO_PREAMBLE_SYMBOLS = 8;

static constexpr size_t MAX_TX_PAYLOAD = 240;
static constexpr size_t MAX_RX_PAYLOAD = 255;
static constexpr size_t SERIAL_LINE_BYTES = 512;

static constexpr uint8_t HW2_MAGIC_0 = 'H';
static constexpr uint8_t HW2_MAGIC_1 = '2';
static constexpr uint8_t HW2_VERSION = 1;
static constexpr uint8_t HW2_TYPE_PING = 1;
static constexpr uint8_t HW2_TYPE_PONG = 2;
static constexpr size_t HW2_HEADER_BYTES = 10;
static constexpr size_t HW2_MIN_FRAME_BYTES = 16;
static constexpr uint32_t HW2_MIN_TIMEOUT_MS = 100;
static constexpr uint32_t HW2_MAX_TIMEOUT_MS = 15000;
static constexpr uint8_t HW2_TIMING_TRACE_VERSION = 1;
static constexpr uint8_t HW3_SCHEDULER_TRACE_VERSION = 1;
static constexpr uint32_t RADIO_MUTEX_TIMEOUT_MS = 5000;
static constexpr uint32_t RESPONDER_TASK_STACK_WORDS = 8192;
static constexpr UBaseType_t RESPONDER_TASK_PRIORITY = 3;
static constexpr BaseType_t RESPONDER_TASK_CORE = 1;
static constexpr uint8_t SERIAL_IDLE_DELAY_MS = 1;

SX1276 radio = new Module(
    RADIO_CS_PIN,
    RADIO_DIO0_PIN,
    RADIO_RST_PIN,
    RADIO_DIO1_PIN
);

volatile bool packetReceived = false;
volatile uint32_t packetReceivedIrqUs = 0;
volatile uint32_t taskWaitCount = 0;
volatile uint32_t taskWakeCount = 0;
volatile uint32_t taskSpuriousWakeCount = 0;
volatile uint32_t taskMutexTimeoutCount = 0;

TaskHandle_t responderTaskHandle = nullptr;
SemaphoreHandle_t radioMutex = nullptr;

char serialLine[SERIAL_LINE_BYTES];
size_t serialLineLength = 0;
bool serialDiscarding = false;

void onPacketReceived() {
    packetReceivedIrqUs = micros();
    packetReceived = true;

    BaseType_t higherPriorityTaskWoken = pdFALSE;
    if (responderTaskHandle != nullptr) {
        vTaskNotifyGiveFromISR(responderTaskHandle, &higherPriorityTaskWoken);
        if (higherPriorityTaskWoken == pdTRUE) {
            portYIELD_FROM_ISR();
        }
    }
}

bool takeRadioMutex() {
    return radioMutex != nullptr &&
           xSemaphoreTake(
               radioMutex,
               pdMS_TO_TICKS(RADIO_MUTEX_TIMEOUT_MS)
           ) == pdTRUE;
}

void giveRadioMutex() {
    if (radioMutex != nullptr) {
        xSemaphoreGive(radioMutex);
    }
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
    Serial.print(MAX_TX_PAYLOAD);
    Serial.print(F(" lab=hw-003 measurement_ping=1 timing_trace=1 timing_trace_version="));
    Serial.print(HW2_TIMING_TRACE_VERSION);
    Serial.print(F(" event_driven_rx=1 scheduler_trace=1 scheduler_trace_version="));
    Serial.print(HW3_SCHEDULER_TRACE_VERSION);
    Serial.print(F(" serial_idle_delay_ms="));
    Serial.print(SERIAL_IDLE_DELAY_MS);
    Serial.print(F(" task_wait_count="));
    Serial.print(taskWaitCount);
    Serial.print(F(" task_wake_count="));
    Serial.print(taskWakeCount);
    Serial.print(F(" task_spurious_wake_count="));
    Serial.print(taskSpuriousWakeCount);
    Serial.print(F(" task_mutex_timeout_count="));
    Serial.println(taskMutexTimeoutCount);
}

bool resumeReceiveLocked() {
    const int16_t state = radio.startReceive();
    if (state != RADIOLIB_ERR_NONE) {
        Serial.print(F("RXSTARTERR "));
        Serial.println(state);
        return false;
    }
    return true;
}

int16_t transmitWithoutRxIsrLocked(const uint8_t *payload, size_t length) {
    packetReceived = false;
    packetReceivedIrqUs = 0;
    radio.clearPacketReceivedAction();
    radio.standby();
    const int16_t state = radio.transmit(payload, length);
    radio.setPacketReceivedAction(onPacketReceived);
    return state;
}

uint16_t readU16(const uint8_t *data) {
    return static_cast<uint16_t>(data[0]) |
           (static_cast<uint16_t>(data[1]) << 8);
}

void writeU16(uint8_t *data, uint16_t value) {
    data[0] = static_cast<uint8_t>(value & 0xFF);
    data[1] = static_cast<uint8_t>((value >> 8) & 0xFF);
}

uint16_t crc16Ccitt(const uint8_t *data, size_t length) {
    uint16_t crc = 0xFFFF;
    for (size_t index = 0; index < length; ++index) {
        crc ^= static_cast<uint16_t>(data[index]) << 8;
        for (uint8_t bit = 0; bit < 8; ++bit) {
            crc = (crc & 0x8000)
                ? static_cast<uint16_t>((crc << 1) ^ 0x1021)
                : static_cast<uint16_t>(crc << 1);
        }
    }
    return crc;
}

uint8_t measurementPatternByte(uint16_t sequence, size_t index) {
    const uint32_t mixed = static_cast<uint32_t>(sequence) * 131u +
                           static_cast<uint32_t>(index) * 17u + 0x5Au;
    return static_cast<uint8_t>(mixed & 0xFFu);
}

void buildMeasurementPing(uint8_t *frame, size_t length, uint16_t sequence) {
    memset(frame, 0, length);
    frame[0] = HW2_MAGIC_0;
    frame[1] = HW2_MAGIC_1;
    frame[2] = HW2_VERSION;
    frame[3] = HW2_TYPE_PING;
    writeU16(frame + 4, sequence);
    frame[8] = 0;
    frame[9] = 0;

    for (size_t index = HW2_HEADER_BYTES; index < length; ++index) {
        frame[index] = measurementPatternByte(sequence, index);
    }
    writeU16(frame + 6, crc16Ccitt(frame + HW2_HEADER_BYTES, length - HW2_HEADER_BYTES));
}

bool isMeasurementFrame(const uint8_t *frame, size_t length, uint8_t expectedType) {
    if (length < HW2_MIN_FRAME_BYTES || length > MAX_TX_PAYLOAD) {
        return false;
    }
    if (frame[0] != HW2_MAGIC_0 || frame[1] != HW2_MAGIC_1 ||
        frame[2] != HW2_VERSION || frame[3] != expectedType) {
        return false;
    }
    const uint16_t expected = readU16(frame + 6);
    const uint16_t actual = crc16Ccitt(frame + HW2_HEADER_BYTES, length - HW2_HEADER_BYTES);
    return expected == actual;
}

uint8_t encodeRssi(float rssiDbm) {
    int encoded = static_cast<int>(roundf(rssiDbm)) + 200;
    if (encoded < 0) {
        encoded = 0;
    } else if (encoded > 255) {
        encoded = 255;
    }
    return static_cast<uint8_t>(encoded);
}

float decodeRssi(uint8_t encoded) {
    return static_cast<float>(static_cast<int>(encoded) - 200);
}

uint8_t encodeSnr(float snrDb) {
    int encoded = static_cast<int>(roundf(snrDb * 4.0f));
    if (encoded < -128) {
        encoded = -128;
    } else if (encoded > 127) {
        encoded = 127;
    }
    return static_cast<uint8_t>(static_cast<int8_t>(encoded));
}

float decodeSnr(uint8_t encoded) {
    const int8_t signedValue = static_cast<int8_t>(encoded);
    return static_cast<float>(signedValue) / 4.0f;
}

void printMeasurementFailure(
    uint16_t sequence,
    size_t frameBytes,
    const char *error,
    uint32_t rttUs,
    uint32_t txBlockUs,
    uint32_t toaUs,
    int16_t state
) {
    Serial.print(F("MRESULT seq="));
    Serial.print(sequence);
    Serial.print(F(" bytes="));
    Serial.print(frameBytes);
    Serial.print(F(" success=0 error="));
    Serial.print(error);
    Serial.print(F(" rtt_us="));
    Serial.print(rttUs);
    Serial.print(F(" tx_block_us="));
    Serial.print(txBlockUs);
    Serial.print(F(" toa_us="));
    Serial.print(toaUs);
    Serial.print(F(" state="));
    Serial.println(state);
}

void printMeasurementSuccess(
    uint16_t sequence,
    size_t frameBytes,
    uint32_t rttUs,
    uint32_t txBlockUs,
    uint32_t toaUs,
    float remoteRssi,
    float remoteSnr,
    float localRssi,
    float localSnr
) {
    Serial.print(F("MRESULT seq="));
    Serial.print(sequence);
    Serial.print(F(" bytes="));
    Serial.print(frameBytes);
    Serial.print(F(" success=1 rtt_us="));
    Serial.print(rttUs);
    Serial.print(F(" tx_block_us="));
    Serial.print(txBlockUs);
    Serial.print(F(" toa_us="));
    Serial.print(toaUs);
    Serial.print(F(" remote_rssi_dbm="));
    Serial.print(remoteRssi, 1);
    Serial.print(F(" remote_snr_db="));
    Serial.print(remoteSnr, 2);
    Serial.print(F(" local_rssi_dbm="));
    Serial.print(localRssi, 1);
    Serial.print(F(" local_snr_db="));
    Serial.println(localSnr, 2);
}

void performMeasurementLocked(uint16_t sequence, size_t frameBytes, uint32_t timeoutMs) {
    uint8_t ping[MAX_TX_PAYLOAD];
    uint8_t pong[MAX_RX_PAYLOAD];
    memset(pong, 0, sizeof(pong));
    buildMeasurementPing(ping, frameBytes, sequence);

    const uint32_t expectedToaUs = static_cast<uint32_t>(radio.getTimeOnAir(frameBytes));

    packetReceived = false;
    packetReceivedIrqUs = 0;
    radio.clearPacketReceivedAction();
    radio.standby();

    const uint32_t startedUs = micros();
    const int16_t txState = radio.transmit(ping, frameBytes);
    const uint32_t txDoneUs = micros();
    const uint32_t txBlockUs = txDoneUs - startedUs;

    if (txState != RADIOLIB_ERR_NONE) {
        radio.setPacketReceivedAction(onPacketReceived);
        resumeReceiveLocked();
        printMeasurementFailure(
            sequence, frameBytes, "tx", txBlockUs, txBlockUs,
            expectedToaUs, txState
        );
        return;
    }

    const int16_t rxState = radio.receive(pong, 0, timeoutMs);
    const uint32_t completedUs = micros();
    const uint32_t rttUs = completedUs - startedUs;

    size_t receivedLength = 0;
    float localRssi = 0.0f;
    float localSnr = 0.0f;
    if (rxState == RADIOLIB_ERR_NONE) {
        receivedLength = radio.getPacketLength();
        localRssi = radio.getRSSI();
        localSnr = radio.getSNR();
    }

    radio.setPacketReceivedAction(onPacketReceived);
    resumeReceiveLocked();

    if (rxState == RADIOLIB_ERR_RX_TIMEOUT) {
        printMeasurementFailure(
            sequence, frameBytes, "timeout", rttUs, txBlockUs,
            expectedToaUs, rxState
        );
        return;
    }
    if (rxState != RADIOLIB_ERR_NONE) {
        printMeasurementFailure(
            sequence, frameBytes, "rx", rttUs, txBlockUs,
            expectedToaUs, rxState
        );
        return;
    }
    if (receivedLength != frameBytes ||
        !isMeasurementFrame(pong, receivedLength, HW2_TYPE_PONG) ||
        readU16(pong + 4) != sequence) {
        printMeasurementFailure(
            sequence, frameBytes, "bad-pong", rttUs, txBlockUs,
            expectedToaUs, 0
        );
        return;
    }

    const float remoteRssi = decodeRssi(pong[8]);
    const float remoteSnr = decodeSnr(pong[9]);
    digitalWrite(BOARD_LED, !digitalRead(BOARD_LED));
    printMeasurementSuccess(
        sequence, frameBytes, rttUs, txBlockUs, expectedToaUs,
        remoteRssi, remoteSnr, localRssi, localSnr
    );
}

bool replyToMeasurementPingLocked(
    const uint8_t *received,
    size_t length,
    float observedRssi,
    float observedSnr,
    uint32_t rxIrqUs,
    uint32_t handlerStartUs,
    uint32_t readDoneUs
) {
    if (!isMeasurementFrame(received, length, HW2_TYPE_PING)) {
        return false;
    }

    uint8_t pong[MAX_TX_PAYLOAD];
    memcpy(pong, received, length);
    pong[3] = HW2_TYPE_PONG;
    pong[8] = encodeRssi(observedRssi);
    pong[9] = encodeSnr(observedSnr);

    const uint16_t sequence = readU16(received + 4);
    const uint32_t expectedToaUs = static_cast<uint32_t>(radio.getTimeOnAir(length));
    const uint32_t txStartUs = micros();
    const int16_t state = transmitWithoutRxIsrLocked(pong, length);
    const uint32_t txDoneUs = micros();

    const uint32_t irqToHandleUs = handlerStartUs - rxIrqUs;
    const uint32_t handleToReadDoneUs = readDoneUs - handlerStartUs;
    const uint32_t readDoneToTxStartUs = txStartUs - readDoneUs;
    const uint32_t irqToTxStartUs = txStartUs - rxIrqUs;
    const uint32_t txBlockUs = txDoneUs - txStartUs;
    const uint32_t irqToTxDoneUs = txDoneUs - rxIrqUs;

    Serial.print(F("H2RESP seq="));
    Serial.print(sequence);
    Serial.print(F(" bytes="));
    Serial.print(length);
    Serial.print(F(" rssi_dbm="));
    Serial.print(observedRssi, 1);
    Serial.print(F(" snr_db="));
    Serial.print(observedSnr, 2);
    Serial.print(F(" toa_us="));
    Serial.print(expectedToaUs);
    Serial.print(F(" state="));
    Serial.print(state);
    Serial.print(F(" timing_v="));
    Serial.print(HW2_TIMING_TRACE_VERSION);
    Serial.print(F(" irq_to_handle_us="));
    Serial.print(irqToHandleUs);
    Serial.print(F(" handle_to_read_done_us="));
    Serial.print(handleToReadDoneUs);
    Serial.print(F(" read_done_to_tx_start_us="));
    Serial.print(readDoneToTxStartUs);
    Serial.print(F(" irq_to_tx_start_us="));
    Serial.print(irqToTxStartUs);
    Serial.print(F(" tx_block_us="));
    Serial.print(txBlockUs);
    Serial.print(F(" irq_to_tx_done_us="));
    Serial.print(irqToTxDoneUs);
    Serial.print(F(" sched_v="));
    Serial.print(HW3_SCHEDULER_TRACE_VERSION);
    Serial.print(F(" task_wait_count="));
    Serial.print(taskWaitCount);
    Serial.print(F(" task_wake_count="));
    Serial.print(taskWakeCount);
    Serial.print(F(" task_spurious_wake_count="));
    Serial.println(taskSpuriousWakeCount);
    return true;
}

void handleReceivedPacketLocked() {
    if (!packetReceived) {
        return;
    }

    const uint32_t rxIrqUs = packetReceivedIrqUs;
    packetReceived = false;
    const uint32_t handlerStartUs = micros();

    const size_t length = radio.getPacketLength();
    uint8_t payload[MAX_RX_PAYLOAD];
    if (length == 0 || length > sizeof(payload)) {
        Serial.print(F("RXERR invalid-length="));
        Serial.println(length);
        resumeReceiveLocked();
        return;
    }

    const int16_t state = radio.readData(payload, length);
    const uint32_t readDoneUs = micros();
    if (state == RADIOLIB_ERR_NONE) {
        const float observedRssi = radio.getRSSI();
        const float observedSnr = radio.getSNR();

        if (replyToMeasurementPingLocked(
                payload,
                length,
                observedRssi,
                observedSnr,
                rxIrqUs,
                handlerStartUs,
                readDoneUs
            )) {
            digitalWrite(BOARD_LED, !digitalRead(BOARD_LED));
            resumeReceiveLocked();
            return;
        }

        digitalWrite(BOARD_LED, !digitalRead(BOARD_LED));
        Serial.print(F("RX "));
        Serial.print(length);
        Serial.print(' ');
        Serial.print(observedRssi, 1);
        Serial.print(' ');
        Serial.print(observedSnr, 1);
        Serial.print(' ');
        printHex(payload, length);
        Serial.println();
    } else if (state == RADIOLIB_ERR_CRC_MISMATCH) {
        Serial.println(F("RXERR crc"));
    } else {
        Serial.print(F("RXERR state="));
        Serial.println(state);
    }

    resumeReceiveLocked();
}

void responderTaskMain(void *) {
    for (;;) {
        ++taskWaitCount;
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        ++taskWakeCount;

        if (!packetReceived) {
            ++taskSpuriousWakeCount;
            continue;
        }

        if (!takeRadioMutex()) {
            ++taskMutexTimeoutCount;
            continue;
        }
        handleReceivedPacketLocked();
        giveRadioMutex();
    }
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
    if (strcmp(line, "SCHED") == 0) {
        Serial.print(F("SCHED v="));
        Serial.print(HW3_SCHEDULER_TRACE_VERSION);
        Serial.print(F(" wait_count="));
        Serial.print(taskWaitCount);
        Serial.print(F(" wake_count="));
        Serial.print(taskWakeCount);
        Serial.print(F(" spurious_wake_count="));
        Serial.print(taskSpuriousWakeCount);
        Serial.print(F(" mutex_timeout_count="));
        Serial.println(taskMutexTimeoutCount);
        return;
    }

    if (strncmp(line, "TOA ", 4) == 0) {
        unsigned long bytesValue = 0;
        char extra = '\0';
        if (sscanf(line + 4, "%lu %c", &bytesValue, &extra) != 1 ||
            bytesValue < 1 || bytesValue > MAX_TX_PAYLOAD) {
            Serial.println(F("ERR invalid-toa-length"));
            return;
        }
        if (!takeRadioMutex()) {
            Serial.println(F("ERR radio-busy"));
            return;
        }
        const uint32_t toaUs = static_cast<uint32_t>(
            radio.getTimeOnAir(static_cast<size_t>(bytesValue))
        );
        giveRadioMutex();
        Serial.print(F("TOA bytes="));
        Serial.print(bytesValue);
        Serial.print(F(" us="));
        Serial.println(toaUs);
        return;
    }

    if (strncmp(line, "MPING ", 6) == 0) {
        unsigned long sequenceValue = 0;
        unsigned long bytesValue = 0;
        unsigned long timeoutValue = 0;
        char extra = '\0';
        if (sscanf(
                line + 6,
                "%lu %lu %lu %c",
                &sequenceValue,
                &bytesValue,
                &timeoutValue,
                &extra
            ) != 3 ||
            sequenceValue > 65535UL ||
            bytesValue < HW2_MIN_FRAME_BYTES || bytesValue > MAX_TX_PAYLOAD ||
            timeoutValue < HW2_MIN_TIMEOUT_MS || timeoutValue > HW2_MAX_TIMEOUT_MS) {
            Serial.println(F("ERR invalid-mping"));
            return;
        }
        if (!takeRadioMutex()) {
            Serial.println(F("ERR radio-busy"));
            return;
        }
        performMeasurementLocked(
            static_cast<uint16_t>(sequenceValue),
            static_cast<size_t>(bytesValue),
            static_cast<uint32_t>(timeoutValue)
        );
        giveRadioMutex();
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
    if (!takeRadioMutex()) {
        Serial.println(F("ERR radio-busy"));
        return;
    }
    const int16_t state = transmitWithoutRxIsrLocked(payload, payloadLength);
    if (state == RADIOLIB_ERR_NONE) {
        digitalWrite(BOARD_LED, !digitalRead(BOARD_LED));
        Serial.print(F("TXOK "));
        Serial.println(payloadLength);
    } else {
        Serial.print(F("TXERR "));
        Serial.println(state);
    }
    resumeReceiveLocked();
    giveRadioMutex();
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

void setup() {
    pinMode(BOARD_LED, OUTPUT);
    digitalWrite(BOARD_LED, LOW);
    Serial.begin(115200);
    delay(200);

    radioMutex = xSemaphoreCreateMutex();
    if (radioMutex == nullptr) {
        Serial.println(F("FATAL radio-mutex"));
        while (true) {
            delay(1000);
        }
    }

    SPI.begin(RADIO_SCLK_PIN, RADIO_MISO_PIN, RADIO_MOSI_PIN);

    if (!takeRadioMutex()) {
        Serial.println(F("FATAL radio-mutex-timeout"));
        while (true) {
            delay(1000);
        }
    }
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
    giveRadioMutex();

    if (state != RADIOLIB_ERR_NONE) {
        Serial.print(F("FATAL radio-init="));
        Serial.println(state);
        while (true) {
            delay(1000);
        }
    }

    const BaseType_t taskState = xTaskCreatePinnedToCore(
        responderTaskMain,
        "hw003-rx",
        RESPONDER_TASK_STACK_WORDS,
        nullptr,
        RESPONDER_TASK_PRIORITY,
        &responderTaskHandle,
        RESPONDER_TASK_CORE
    );
    if (taskState != pdPASS || responderTaskHandle == nullptr) {
        Serial.println(F("FATAL responder-task"));
        while (true) {
            delay(1000);
        }
    }

    if (!takeRadioMutex()) {
        Serial.println(F("FATAL radio-mutex-timeout"));
        while (true) {
            delay(1000);
        }
    }
    radio.setPacketReceivedAction(onPacketReceived);
    const bool receiveStarted = resumeReceiveLocked();
    giveRadioMutex();
    if (!receiveStarted) {
        while (true) {
            delay(1000);
        }
    }

    Serial.println(F("READY hw-003"));
    printInfo();
}

void loop() {
    handleSerial();
    delay(SERIAL_IDLE_DELAY_MS);
}
