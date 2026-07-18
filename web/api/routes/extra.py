"""Backward-compat stub — routes have been split into:
- interfaces.py     (interfaces, routing, tunnels, VLANs)
- firewall.py       (ARP, firewall rules CRUD)
- network_services.py (netflow, DHCP relay, hotspot, config export)
- system_extra.py   (logs, protocol events, scheduler, setup, certs)

See web/api/routes/__init__.py for the new module list.
"""

from fastapi import APIRouter

router = APIRouter(tags=["Network"])
