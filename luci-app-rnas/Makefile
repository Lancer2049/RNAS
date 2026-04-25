include $(TOPDIR)/rules.mk

PKG_NAME:=luci-app-rnas
PKG_VERSION:=1.0
PKG_RELEASE:=1
PKG_LICENSE:=GPL-2.0

LUCI_TITLE:=LuCI support for RADIUS NAS (accel-ppp)
LUCI_DEPENDS:=+luci-base +uhttpd +luci-lib-nixio +accel-ppp
LUCI_PKGARCH:=all

define Package/luci-app-rnas
  TITLE:=$(LUCI_TITLE)
  SECTION:=applications
  CATEGORY:=LuCI
  SUBMENU:=VPN
  URL:=https://github.com/Lancer2049/RNAS
  MAINTAINER:=Lancer2049
  DEPENDS:=$(LUCI_DEPENDS)
  PKGARCH:=$(LUCI_PKGARCH)
endef

define Package/luci-app-rnas/description
	LuCI application for managing RADIUS NAS (accel-ppp).
	Provides web interface for:
	- RADIUS server configuration
	- Protocol settings (PPPoE, IPoE, L2TP, PPTP, SSTP)
	- IP address pool management
	- Session monitoring and management
	- CoA (Change of Authorization) control
endef

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
endef

define Build/Configure
endef

define Build/Compile
endef

define Package/luci-app-rnas/install
	$(CP) ./luasrc/* $(1)/usr/lib/lua/luci/
	$(CP) ./root/* $(1)/

	find $(1) -name '*.lua' -exec chmod 644 {} \;
	find $(1) -name '*.htm' -exec chmod 644 {} \;
	find $(1) -name '*.json' -exec chmod 644 {} \;
	find $(1) -name '*.sh' -exec chmod 755 {} \;
	find $(1) -name 'Makefile' -exec chmod 644 {} \;
endef

define Package/luci-app-rnas/postinst
#!/bin/sh
[ -n "${IPKG_INSTROOT}" ] || {
	/etc/init.d/accel-ppp-rnas enabled && /etc/init.d/accel-ppp-rnas reload 2>/dev/null || true
	/etc/init.d/uhttpd reload 2>/dev/null || true
}
exit 0
endef

define Package/luci-app-rnas/prerm
#!/bin/sh
[ -n "${IPKG_INSTROOT}" ] || {
	/etc/init.d/accel-ppp-rnas disable 2>/dev/null || true
}
exit 0
endef

$(eval $(call BuildPackage,luci-app-rnas))
