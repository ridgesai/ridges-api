from fastapi import FastAPI, Request
from typing import Dict, Any, List

app = FastAPI()

@app.post("/logs")
async def process_logs(request: Request, data: List[Dict[str, Any]]):
    headers = dict(request.headers)
    print(headers["validator-hotkey"])
    print(data)
    return {
        "status": "success",
        "received_data": data,
        "headers": headers
    }

@app.post("/availability-checks")
async def process_availability_checks(request: Request, data: List[Dict[str, Any]]):
    headers = dict(request.headers)
    print(headers["validator-hotkey"])
    print(data)
    return {
        "status": "success",
        "received_data": data,
        "headers": headers
    }

@app.post("challenge-assignments")
async def process_challenge_assignments(request: Request, data: List[Dict[str, Any]]):
    headers = dict(request.headers)
    print(headers["validator-hotkey"])
    print(data)
    return {
        "status": "success",
        "received_data": data,
        "headers": headers
    }

@app.post("/codegen-challenges")
async def process_codegen_challenges(request: Request, data: List[Dict[str, Any]]):
    headers = dict(request.headers)
    print(headers["validator-hotkey"])
    print(data)
    return {
        "status": "success",
        "received_data": data,
        "headers": headers
    }

@app.post("/responses")
async def process_responses(request: Request, data: List[Dict[str, Any]]):
    headers = dict(request.headers)
    print(headers["validator-hotkey"])
    print(data)
    return {
        "status": "success",
        "received_data": data,
        "headers": headers
    }
