#
# Copyright (C) 2024 RNAS Project
#
# This is free software, licensed under the GNU General Public License v2.
#

include $(TOPDIR)/rules.mk

PKG_NAME:=accel-ppp
PKG_VERSION:=1.13.0
PKG_RELEASE:=1

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://github.com/accel-ppp/accel-ppp.git
PKG_SOURCE_DATE:=2024-01-15
PKG_SOURCE_VERSION:=HEAD
PKG_MIRROR_HASH:=skip

PKG_MAINTAINER:=RNAS Project
PKG_LICENSE:=GPL-2.0-only
PKG_LICENSE_FILES:=COPYING

PKG_BUILD_PARALLEL:=1
PKG_INSTALL:=1

include $(INCLUDE_DIR)/package.mk
include $(INCLUDE_DIR)/cmake.mk

define Package/accel-ppp/config
	source "$(SOURCE)/Config.in"
endef

define Package/accel-ppp
  SECTION:=net
  CATEGORY:=Network
  TITLE:=High-performance PPPoE/IPoE/L2TP/PPTP VPN server with RADIUS
  URL:=https://github.com/accel-ppp/accel-ppp
  DEPENDS:=+libpthread +librt +libubus +libblobmsg-json +kmod-tun
endef

define Package/accel-ppp/description
  accel-ppp is a high-performance VPN server platform supporting:
  - PPPoE (Point-to-Point Protocol over Ethernet)
  - IPoE (IP over Ethernet / DHCP+)
  - L2TP (Layer 2 Tunneling Protocol)
  - PPTP (Point-to-Point Tunneling Protocol)
  - SSTP (Secure Socket Tunneling Protocol)
  - RADIUS authentication, accounting, and CoA
endef

define Package/accel-ppp/conffiles
/etc/config/rnas
endef

CMAKE_OPTIONS += \
	-DCMAKE_BUILD_TYPE=Release \
	-DBUILD_PPPOE=yes \
	-DBUILD_IPOE=yes \
	-DBUILD_L2TP=yes \
	-DBUILD_PPTP=yes \
	-DBUILD_SSTP=yes \
	-DBUILD_RADIUS=yes \
	-DBUILD_VLAN=yes \
	-DBUILD_IPPOOL=yes \
	-DLOG_FILE=yes \
	-DLOG_SYSLOG=yes \
	-DLOG_PGSQL=no \
	-DLOG_MYSQL=no \
	-DLOG_SQLITE=yes \
	-DCRYPTO=openssl \
	-DCPACK_TYPE=openwrt

define Build/Prepare
	$(call Build/Prepare/Default)
	rm -rf $(PKG_BUILD_DIR)/configs
endef

define Package/accel-ppp/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) $(PKG_INSTALL_DIR)/usr/sbin/accel-pppd $(1)/usr/sbin/
	$(INSTALL_BIN) $(PKG_INSTALL_DIR)/usr/sbin/accel-cmd $(1)/usr/sbin/

	# Install RADIUS client tools
	$(INSTALL_BIN) $(PKG_INSTALL_DIR)/usr/bin/radclient $(1)/usr/sbin/

	# Install UCI configuration defaults
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DATA) ../../root/etc/config/rnas $(1)/etc/config/rnas

	# Install procd init script
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ../../root/etc/init.d/accel-ppp $(1)/etc/init.d/accel-ppp

	# Install UCI translation utility
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) ../../root/usr/sbin/accel-ppp-uci $(1)/usr/sbin/accel-ppp-uci

	# Install uci-defaults for first-boot setup
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_DATA) ../../root/etc/uci-defaults/rnas $(1)/etc/uci-defaults/rnas

	# Install configs
	$(INSTALL_DIR) $(1)/etc/accel-ppp
endef

define Package/accel-ppp/postinst
#!/bin/sh
[ -n "$${IPKG_INSTROOT}" ] || {
	/etc/init.d/accel-ppp enable 2>/dev/null || true
}
exit 0
endef

$(eval $(call BuildPackage,accel-ppp))
