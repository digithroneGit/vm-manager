#!/usr/bin/env python3
import os
import asyncio
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query, APIRouter
from dotenv import load_dotenv
from models import ActionPost

load_dotenv(".env")

VERSION = os.getenv("VERSION", "v1")

app = FastAPI(version=VERSION)
router = APIRouter(prefix=f"/v{VERSION}")

DEFAULT_TIMEOUT = 5.0


def get_worker_hosts() -> List[str]:
    raw = os.getenv("WORKER_HOSTS", "")
    return [h.strip() for h in raw.split(",") if h.strip()]


@app.on_event("startup")
async def startup():
    app.state.status = "starting"
    workers = get_worker_hosts()
    print("WORKERS INITIALIZED: "+str(workers))
    n = max(1, len(workers))
    limits = httpx.Limits(max_connections=n, max_keepalive_connections=n)
    app.state.http = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, limits=limits)
    app.state.semaphore = asyncio.Semaphore(n)
    app.state.worker_count = n
    app.state.status = "healthy" if workers else "unhealthy"
    app.state.version = VERSION


@app.on_event("shutdown")
async def shutdown():
    client: Optional[httpx.AsyncClient] = getattr(app.state, "http", None)
    if client:
        await client.aclose()


async def semaphore_fetch(awaitable, semaphore: asyncio.Semaphore):
    async with semaphore:
        return await awaitable


async def get_vms(client: httpx.AsyncClient, semaphore: asyncio.Semaphore, host: str) -> List[Dict[str, Any]]:
    try:
        resp = await semaphore_fetch(client.get(f"http://{host}/vms"), semaphore)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[ERROR] {host} GET /vms failed: {e}")
        return []


async def get_vm_from_worker(client: httpx.AsyncClient, semaphore: asyncio.Semaphore, host: str, name: str):
    try:
        resp = await semaphore_fetch(client.get(f"http://{host}/vms/{name}"), semaphore)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else [data]
    except Exception as e:
        print(f"[ERROR] {host} GET /vms/{name} failed: {e}")
        return []


async def post_vm_cmd_to_worker(client, semaphore, host, name, body: ActionPost):
    try:
        resp = await semaphore_fetch(client.post(f"http://{host}/vms/{name}", json=body.model_dump()), semaphore)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] {host} POST /vms/{name} {body.state} failed: {e}")
        return None


#rute
@router.get("/vms", response_model=List[Dict[str, Any]])
async def get_all_domains():
    workers = get_worker_hosts()
    if not workers:
        app.state.status = "unhealthy"
        raise HTTPException(status_code=422, detail="No WORKER_HOSTS configured")

    client: httpx.AsyncClient = app.state.http
    semaphore: asyncio.Semaphore = app.state.semaphore
    tasks = []
    for worker in workers:
        print(f"Requesting VM list from worker {worker}...")
        task = get_vms(client, semaphore, worker)
        tasks.append(task)

    results_nested = await asyncio.gather(*tasks)
    results = [item for sub in results_nested for item in sub]
    if not results:
        raise HTTPException(status_code=404, detail="No domains found")
    return results


@router.get("/vms/{name}", response_model=List[Dict[str, Any]])
async def get_domain_from_all(name: str):
    workers = get_worker_hosts()
    if not workers:
        app.state.status = "unhealthy"
        raise HTTPException(status_code=422, detail="No WORKER_HOSTS configured")
    client: httpx.AsyncClient = app.state.http
    semaphore: asyncio.Semaphore = app.state.semaphore
    tasks = []
    for worker in workers:
        task = get_vm_from_worker(client, semaphore, worker, name)
        tasks.append(task)

    nested = await asyncio.gather(*tasks)
        
    results = [item for sub in nested for item in sub]
    if not results:
        raise HTTPException(status_code=404, detail=f"Domain '{name}' not found")
    return results


@router.post("/vms/{name}", response_model=List[Dict[str, Any]])
async def post_vm_cmd(name: str, body: ActionPost, host: Optional[str] = Query(default=None)):
    workers = get_worker_hosts()
    if not workers:
        app.state.status = "unhealthy"
        raise HTTPException(status_code=422, detail="No WORKER_HOSTS configured")
    client: httpx.AsyncClient = app.state.http
    semaphore: asyncio.Semaphore = app.state.semaphore
    targets = [host] if host else workers
    tasks = []
    for worker in targets:
        result = post_vm_cmd_to_worker(client, semaphore, worker, name, body) #maybe could be lambda instead
        tasks.append(result)
    nested = await asyncio.gather(*tasks)
    results = [r for r in nested if r is not None]
    if not results:
        raise HTTPException(status_code=404, detail=f"No worker executed '{body.state}' on '{name}'")
    return results


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": getattr(app.state, "status", "unknown"),
        "version": getattr(app.state, "version", "unknown")
    }

#add version prefix
app.include_router(router)
