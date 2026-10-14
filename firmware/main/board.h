// Rack ATX controller B.2 -- board definitions derived from hardware/circuit.json (revision B.2).
// Pin numbers are ESP32-S3 GPIO numbers. Verify against the released schematic before flashing.
#pragma once

#define FW_VERSION "b2-0.1.0"

// MCU GPIO map (circuit.json "gpio" table, B.2)
#define PIN_BOOT_N          0   // strapping, external 10k pull-up
#define PIN_TIMER_ARM       4   // MC14541B MR release + Q200 gate; active high; 10k pull-down
#define PIN_OUT_OE_N        6   // 74HC595 OE, active low; external 10k pull-up
#define PIN_OUT_LATCH       7   // 74HC595 RCLK; external 100k pull-down
#define PIN_USB_VBUS_SENSE  33  // input, informational only
#define PIN_SPI_SCK         39  // SPI_SCK_RAW -> 47R -> SPI_SCK (shared: W5500 + 3x74HC595)
#define PIN_SPI_MOSI        40  // SPI_MOSI_RAW -> 47R -> SPI_MOSI (shared)
#define PIN_SPI_MISO        41  // from W5500 only
#define PIN_ETH_CS_N        42
#define PIN_ETH_RST_N       47
#define PIN_ETH_INT_N       48

// 74HC595 chain: MOSI -> U4 (DRV_01..08) -> U5 (DRV_09..16) -> U6 (DRV_17..20 on QA..QD).
// Shift order on the wire is U6 byte, U5 byte, U4 byte, MSB first; within a device bit0 = QA.
#define SR_DEVICES          3
#define DRV_COUNT           20

// Host h (1..10): POWER = DRV_(2h-1), RESET = DRV_(2h)  (host sheets R39/R43 ... R111/R115)
#define HOST_COUNT          10
#define DRV_POWER(host)     (2u * (host) - 1u)
#define DRV_RESET(host)     (2u * (host))

// Timing limits. The MC14541B window (200k/1nF C0G, 32768 counts) is about 15.07 s and cuts the
// rail regardless of firmware; firmware never requests more than PRESS_MAX_MS.
#define PRESS_MIN_MS        100
#define PRESS_MAX_MS        10000
#define ARM_LOW_GAP_MS      50      // datasheet note on the outputs sheet: ARM low >= 10 ms between commands
#define RAIL_SETTLE_MS      5       // Q4 turn-on + TLP3122A tON (2 ms typ, 3 ms max) is inside the press time

// SPI
#define SPI_HOST_USED       SPI2_HOST
#define ETH_SPI_CLOCK_HZ    (8 * 1000 * 1000)   // HARDWARE.md: start at 8 MHz and verify timing
#define SR_SPI_CLOCK_HZ     (2 * 1000 * 1000)
