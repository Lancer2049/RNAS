"""Simple OUI (MAC vendor) lookup table for common networking vendors."""
OUI = {
    "000c29":"VMware","005056":"VMware","00155d":"Hyper-V","3c970e":"MikroTik",
    "000b6b":"Cisco","001bd4":"Cisco","0021d8":"Cisco","00189b":"Dell",
    "0019b9":"Dell","00016c":"Foxconn","001a6b":"Ubiquiti","000874":"D-Link",
    "00179a":"D-Link","001fc6":"Intel","002241":"Apple","0017f2":"Apple",
    "001ec2":"HP","002481":"HP","000372":"Juniper","0020a2":"Juniper",
    "000e0c":"Intel","000423":"Intel","001e8c":"Huawei","000b82":"Huawei",
    "002128":"H3C","000fe2":"H3C","001bfc":"NVIDIA","003048":"Supermicro",
    "000c41":"Linksys","00173f":"Netgear","001ec7":"TP-Link","002719":"TP-Link",
    "dc4ef4":"MikroTik","00156d":"Ubiquiti","000bc1":"Nokia","0020a6":"Nokia",
    "0050ba":"D-Link","002104":"D-Link","000fb5":"Netgear","0026f2":"Netgear",
    "000af3":"Belkin","00173e":"ASUS","0022b0":"ASUS","001f1f":"Edimax",
}
def lookup(mac: str) -> str:
    prefix = mac.replace(":", "").replace("-", "").lower()[:6]
    return OUI.get(prefix, "")
