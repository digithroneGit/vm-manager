#!/usr/bin/env python3
import os
import asyncio
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


class ActionPost(BaseModel):
    state: str = Field(...)

