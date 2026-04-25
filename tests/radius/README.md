# FreeRADIUS Test Configuration for RNAS-OpenWrt

This directory contains FreeRADIUS configuration files for end-to-end
testing of RADIUS authentication, accounting, and CoA with RNAS-OpenWrt.

## Files

| File | Purpose |
|------|---------|
| `clients.conf` | Authorizes RNAS-OpenWrt NAS (192.168.0.84) as a RADIUS client |
| `users` | Test user accounts with attributes for auth/acct testing |
| `sites/rnas-test` | Virtual server config enabling auth/acct/CoA processing |
| `dictionary.rnas` | (optional) Custom RADIUS attributes if needed |

## Setup

On the FreeRADIUS server (assumed 192.168.1.1):

```bash
# Copy configuration files
sudo cp clients.conf /etc/freeradius/3.0/clients.conf
sudo cp users /etc/freeradius/3.0/users

# Enable the test virtual server
sudo mkdir -p /etc/freeradius/3.0/sites-enabled
sudo ln -sf /etc/freeradius/3.0/sites-available/rnas-test \
            /etc/freeradius/3.0/sites-enabled/rnas-test

# Restart FreeRADIUS
sudo systemctl restart freeradius
```

## Test Users

| Username | Password | Purpose |
|----------|----------|---------|
| `testuser` | `testpass123` | Standard PPPoE user, 3600s session timeout |
| `bwtest` | `bwtest123` | User with bandwidth limits (10M up / 50M down) |
| `statictest` | `statictest123` | User with static IP 10.0.0.200 |
| `rejecttest` | `reject` | User for auth rejection testing |
| `accttest` | `accttest123` | User with 60s interim accounting interval |

## Verification

```bash
# Test authentication
radtest testuser testpass123 127.0.0.1 0 testing123

# Check accounting logs
tail -f /var/log/freeradius/radacct/detail

# Monitor CoA
tail -f /var/log/freeradius/coa-detail
```
