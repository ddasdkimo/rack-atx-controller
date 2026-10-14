#include "eth.h"
#include <string.h>
#include <stdio.h>
#include "esp_log.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_eth.h"
#include "esp_eth_mac.h"
#include "esp_eth_phy.h"
#include "esp_mac.h"
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "board.h"
#include "config.h"

static const char *TAG = "eth";
static esp_netif_t *s_netif;
static esp_eth_handle_t s_eth;
static volatile bool s_link;
static volatile bool s_got_ip;
static esp_netif_ip_info_t s_ip;

static void eth_event(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    switch (id) {
    case ETHERNET_EVENT_CONNECTED:
        s_link = true;
        ESP_LOGI(TAG, "link up");
        break;
    case ETHERNET_EVENT_DISCONNECTED:
        s_link = false;
        s_got_ip = false;
        ESP_LOGW(TAG, "link down");
        break;
    case ETHERNET_EVENT_START:
        ESP_LOGI(TAG, "started");
        break;
    case ETHERNET_EVENT_STOP:
        ESP_LOGW(TAG, "stopped");
        break;
    default:
        break;
    }
}

static void ip_event(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    if (id == IP_EVENT_ETH_GOT_IP) {
        ip_event_got_ip_t *e = (ip_event_got_ip_t *)data;
        s_ip = e->ip_info;
        s_got_ip = true;
        ESP_LOGI(TAG, "ip " IPSTR " gw " IPSTR, IP2STR(&s_ip.ip), IP2STR(&s_ip.gw));
    } else if (id == IP_EVENT_ETH_LOST_IP) {
        s_got_ip = false;
    }
}

esp_err_t eth_init(void)
{
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    spi_bus_config_t bus = {
        .mosi_io_num = PIN_SPI_MOSI,
        .miso_io_num = PIN_SPI_MISO,
        .sclk_io_num = PIN_SPI_SCK,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 4096,
    };
    ESP_ERROR_CHECK(spi_bus_initialize(SPI_HOST_USED, &bus, SPI_DMA_CH_AUTO));

    spi_device_interface_config_t dev = {
        .command_bits = 16,   // W5500 address phase
        .address_bits = 8,    // W5500 control phase
        .mode = 0,
        .clock_speed_hz = ETH_SPI_CLOCK_HZ,
        .spics_io_num = PIN_ETH_CS_N,
        .queue_size = 20,
    };
    eth_w5500_config_t w5500 = ETH_W5500_DEFAULT_CONFIG(SPI_HOST_USED, &dev);
    w5500.int_gpio_num = PIN_ETH_INT_N;

    eth_mac_config_t mac_cfg = ETH_MAC_DEFAULT_CONFIG();
    eth_phy_config_t phy_cfg = ETH_PHY_DEFAULT_CONFIG();
    phy_cfg.reset_gpio_num = PIN_ETH_RST_N;
    phy_cfg.autonego_timeout_ms = 0;   // W5500 reports link itself

    esp_eth_mac_t *mac = esp_eth_mac_new_w5500(&w5500, &mac_cfg);
    esp_eth_phy_t *phy = esp_eth_phy_new_w5500(&phy_cfg);
    if (!mac || !phy) {
        ESP_LOGE(TAG, "W5500 driver objects failed");
        return ESP_FAIL;
    }
    esp_eth_config_t cfg = ETH_DEFAULT_CONFIG(mac, phy);
    ESP_ERROR_CHECK(esp_eth_driver_install(&cfg, &s_eth));

    // W5500 has no burned-in MAC: derive one from the chip's factory base MAC.
    uint8_t macaddr[6];
    ESP_ERROR_CHECK(esp_read_mac(macaddr, ESP_MAC_ETH));
    ESP_ERROR_CHECK(esp_eth_ioctl(s_eth, ETH_CMD_S_MAC_ADDR, macaddr));

    esp_netif_config_t netif_cfg = ESP_NETIF_DEFAULT_ETH();
    s_netif = esp_netif_new(&netif_cfg);
    ESP_ERROR_CHECK(esp_netif_attach(s_netif, esp_eth_new_netif_glue(s_eth)));
    ESP_ERROR_CHECK(esp_event_handler_register(ETH_EVENT, ESP_EVENT_ANY_ID, eth_event, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, ESP_EVENT_ANY_ID, ip_event, NULL));

    if (!g_cfg.dhcp) {
        esp_netif_ip_info_t info = {0};
        if (esp_netif_str_to_ip4(g_cfg.ip, &info.ip) != ESP_OK ||
            esp_netif_str_to_ip4(g_cfg.mask, &info.netmask) != ESP_OK ||
            esp_netif_str_to_ip4(g_cfg.gw, &info.gw) != ESP_OK) {
            ESP_LOGE(TAG, "bad static IP config, falling back to DHCP");
        } else {
            ESP_ERROR_CHECK(esp_netif_dhcpc_stop(s_netif));
            ESP_ERROR_CHECK(esp_netif_set_ip_info(s_netif, &info));
            s_ip = info;
            s_got_ip = true;
            ESP_LOGI(TAG, "static ip %s", g_cfg.ip);
        }
    }
    ESP_ERROR_CHECK(esp_eth_start(s_eth));
    return ESP_OK;
}

bool eth_link_up(void) { return s_link; }
bool eth_has_ip(void) { return s_got_ip; }

void eth_get_ip(char *buf, size_t n)
{
    if (!s_got_ip) {
        snprintf(buf, n, "0.0.0.0");
        return;
    }
    snprintf(buf, n, IPSTR, IP2STR(&s_ip.ip));
}
