#include <Arduino.h>
#include <RadioLib.h>
#include <SPI.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <freertos/task.h>

#define printInfo hw003PrintInfo
#define processCommand hw003ProcessCommand
#define handleSerial hw003HandleSerial
#define setup hw003Setup
#define loop hw003Loop
#include "hw003.cpp"
#undef loop
#undef setup
#undef handleSerial
#undef processCommand
#undef printInfo

// HW-006 keeps the frozen H2/event-driven receive path but boots directly at
// 2 dBm so the remote responder can be powered from a USB power bank without
// requiring a serial command after reset.
static constexpr int8_t HW6_POWER_MIN_DBM = 2;
static constexpr int8_t HW6_POWER_MAX_DBM = 10;
static constexpr int8_t HW6_BOOT_POWER_DBM = 2;
static constexpr uint8_t HW6_POWER_CONTROL_VERSION = 1;
static constexpr uint8_t HW6_UNTETHERED_PROFILE_VERSION = 1;
static int8_t hw6CurrentPowerDbm = HW6_BOOT_POWER_DBM;

void hw006PrintInfo() {
    Serial.print(F("INFO board=lilygo-lora32-v1.6.1 chip=sx1276 freq_mhz="));
    Serial.print(RADIO_FREQUENCY_MHZ, 3);
    Serial.print(F(" bw_khz="));
    Serial.print(RADIO_BANDWIDTH_KHZ, 1);
    Serial.print(F(" sf="));
    Serial.print(RADIO_SPREADING_FACTOR);
    Serial.print(F(" cr=4/"));
    Serial.print(RADIO_CODING_RATE);
    Serial.print(F(" power_dbm="));
    Serial.print(hw6CurrentPowerDbm);
    Serial.print(F(" max_tx="));
    Serial.print(MAX_TX_PAYLOAD);
    Serial.print(F(" lab=hw-006 measurement_ping=1 timing_trace=1 timing_trace_version="));
    Serial.print(HW2_TIMING_TRACE_VERSION);
    Serial.print(F(" event_driven_rx=1 scheduler_trace=1 scheduler_trace_version="));
    Serial.print(HW3_SCHEDULER_TRACE_VERSION);
    Serial.print(F(" power_control=1 power_control_version="));
    Serial.print(HW6_POWER_CONTROL_VERSION);
    Serial.print(F(" power_min_dbm="));
    Serial.print(HW6_POWER_MIN_DBM);
    Serial.print(F(" power_max_dbm="));
    Serial.print(HW6_POWER_MAX_DBM);
    Serial.print(F(" power_path=pa_boost boot_power_dbm="));
    Serial.print(HW6_BOOT_POWER_DBM);
    Serial.print(F(" untethered_responder=1 untethered_profile_version="));
    Serial.print(HW6_UNTETHERED_PROFILE_VERSION);
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

void hw006SetPower(const int8_t powerDbm) {
    if (powerDbm < HW6_POWER_MIN_DBM || powerDbm > HW6_POWER_MAX_DBM) {
        Serial.println(F("ERR invalid-power"));
        return;
    }
    if (!takeRadioMutex()) {
        Serial.println(F("ERR radio-busy"));
        return;
    }

    radio.standby();
    const int16_t state = radio.setOutputPower(powerDbm);
    bool receiveStarted = false;
    if (state == RADIOLIB_ERR_NONE) {
        hw6CurrentPowerDbm = powerDbm;
        receiveStarted = resumeReceiveLocked();
    } else {
        receiveStarted = resumeReceiveLocked();
    }
    giveRadioMutex();

    if (state != RADIOLIB_ERR_NONE) {
        Serial.print(F("ERR power-state="));
        Serial.println(state);
        return;
    }
    if (!receiveStarted) {
        Serial.println(F("ERR power-rx-restart"));
        return;
    }
    Serial.print(F("POWEROK dbm="));
    Serial.println(hw6CurrentPowerDbm);
}

void hw006ProcessCommand(char *line) {
    if (strcmp(line, "INFO") == 0) {
        hw006PrintInfo();
        return;
    }
    if (strncmp(line, "POWER ", 6) == 0) {
        long powerValue = 0;
        char extra = '\0';
        if (sscanf(line + 6, "%ld %c", &powerValue, &extra) != 1 ||
            powerValue < HW6_POWER_MIN_DBM || powerValue > HW6_POWER_MAX_DBM) {
            Serial.println(F("ERR invalid-power"));
            return;
        }
        hw006SetPower(static_cast<int8_t>(powerValue));
        return;
    }
    hw003ProcessCommand(line);
}

void hw006HandleSerial() {
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
                hw006ProcessCommand(serialLine);
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
        HW6_BOOT_POWER_DBM,
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
    hw6CurrentPowerDbm = HW6_BOOT_POWER_DBM;

    const BaseType_t taskState = xTaskCreatePinnedToCore(
        responderTaskMain,
        "hw006-rx",
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

    Serial.println(F("READY hw-006"));
    hw006PrintInfo();
}

void loop() {
    hw006HandleSerial();
    delay(SERIAL_IDLE_DELAY_MS);
}
