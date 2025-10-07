#!/usr/bin/env python3
import sys
import libvirt
from dotenv import load_dotenv
from contextlib import contextmanager
from typing import Dict, List, Any

load_dotenv(".env")

@contextmanager
def qemu_conn():
    conn = None
    try:
        conn = libvirt.open("qemu:///system")
        if conn is None:
            raise RuntimeError(f"Failed to connect to qemu")
        yield conn
    except Exception as e:
        raise RuntimeError(f"[ERROR][libvirt] {e}")
    finally:
        if conn:
            conn.close()


def state_str(state_code: int) -> str:
    states = {
        libvirt.VIR_DOMAIN_NOSTATE:     "no state",
        libvirt.VIR_DOMAIN_RUNNING:     "running",
        libvirt.VIR_DOMAIN_BLOCKED:     "blocked",
        libvirt.VIR_DOMAIN_PAUSED:      "paused",
        libvirt.VIR_DOMAIN_SHUTDOWN:    "shutdown",
        libvirt.VIR_DOMAIN_SHUTOFF:     "off",
        libvirt.VIR_DOMAIN_CRASHED:     "crashed",
        libvirt.VIR_DOMAIN_PMSUSPENDED: "pm suspended",
    }
    return states.get(state_code, f"unknown({state_code})")

def get_domain(conn: libvirt.virConnect, name: str) -> libvirt.virDomain:
    try:
        return conn.lookupByName(name)
    except libvirt.libvirtError:
        raise RuntimeError(f"Domain '{name}' not found")

def get_vm_info(conn: libvirt.virConnect, name: str) -> Dict[str, Any]:
    vm = get_domain(conn, name)
    state_code, _ = vm.state()
    info = vm.info()
    return {
        "name":  vm.name(),
        "uuid":  vm.UUIDString(),
        "state": state_str(state_code),
        "vcpus": int(info[3]),
        "memG":  int(info[2] // (1024 * 1024))
    }

def list_vms(conn: libvirt.virConnect) -> List[Dict[str, Any]]:
    out = []
    for vm in conn.listAllDomains(0):
        try:
            out.append(get_vm_info(conn, vm.name()))
        except Exception as e:
            print(f"[WARNING] get_vm_info({vm.name()}) failed: {e}")
            continue
    return out

def vm_cmd(conn: libvirt.virConnect, name: str, action: str) -> str:
    dom = get_domain(conn, name)
    if action == "start":
        if dom.isActive():
            return f"{name} already running"
        dom.create()
        return f"Started {name}"
    if action == "shutdown":
        if not dom.isActive():
            return f"{name} not running"
        dom.shutdown()
        return f"Shutdown signal sent to {name}"
    if action == "reboot":
        if not dom.isActive():
            return f"{name} not running"
        dom.reboot(0)
        return f"Reboot signal sent to {name}"
    raise ValueError(f"Unsupported action: {action}")
