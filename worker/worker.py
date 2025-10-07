#!/usr/bin/env python3
import os
import libvirt
from typing import List

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from models import VMSummary, VMDetail, VMActionRequest
from virt import list_vms, get_vm_info, qemu_conn

load_dotenv(".env")

version = os.getenv("VERSION")
HOSTNAME = os.getenv("HOSTNAME") or os.uname().nodename
app = FastAPI(version=version)


@app.on_event("startup")
async def startup():
    app.state.status = "healthy"
    app.state.version = version


@app.get("/vms", response_model=List[VMSummary])
def list_all_vms():
    try:
        with qemu_conn() as conn:
            vms = list_vms(conn)
        for vm in vms:
            vm["host"] = HOSTNAME
            vm["FQDN"] = f"{vm['name']}.{HOSTNAME}"
        return vms
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vms/{name}", response_model=VMDetail)
def get_vm(name: str):
    try:
        with qemu_conn() as conn:
            info = get_vm_info(conn, name)
        info["host"] = HOSTNAME
        info["FQDN"] = f"{info['name']}.{HOSTNAME}"
        return info
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vms/{name}", response_model=VMDetail)
def post_vm_cmd(name: str, body: VMActionRequest):
    try:
        with qemu_conn() as conn:
            try:
                dom = conn.lookupByName(name)
            except libvirt.libvirtError as e:
                raise HTTPException(status_code=404, detail=f"VM '{name}' not found: {e}")

            try:
                getattr(dom, body.state)()
            except AttributeError:
                raise HTTPException(status_code=400, detail=f"Unsupported command '{body.state}'")

            info = get_vm_info(conn, dom.name())
            info["host"] = HOSTNAME
            info["FQDN"] = f"{info['name']}.{HOSTNAME}"
            return info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
