# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import List
# import os

# app = FastAPI()

# # Define your case structure for API input
# class Case(BaseModel):
#     case_id: int
#     status: str
#     last_updated: str  # ISO format datetime string

# # Define SLA thresholds
# SLA_PENDING_STAFFING_HOURS = float(os.getenv("SLA_PENDING_STAFFING_HOURS", "48"))

# # Notification function (could be email, SMS, etc.)
# def send_notification(case_id: int, message: str):
#     # Send an email, SMS, or other notifications
#     print(f"Sending notification for case {case_id}: {message}")

# # Function to calculate hours since the last update
# def hours_since(last_updated: str) -> float:
#     # Convert the string to a datetime object
#     last_dt = datetime.fromisoformat(last_updated)
#     now = datetime.now()
#     delta = now - last_dt
#     return delta.total_seconds() / 3600  # return hours

# # Endpoint to check for stalled cases
# @app.post("/check_stalled_cases/")
# async def check_stalled_cases(cases: List[Case]):
#     stalled_cases = []
    
#     for case in cases:
#         # Calculate how many hours have passed since last update
#         idle_hours = hours_since(case.last_updated)
        
#         if case.status == "pending staffing" and idle_hours >= SLA_PENDING_STAFFING_HOURS:
#             stalled_cases.append(case)
#             send_notification(case.case_id, f"Case {case.case_id} is pending staffing for more than {SLA_PENDING_STAFFING_HOURS} hours.")
    
#     if stalled_cases:
#         return {"status": "success", "stalled_cases": [case.case_id for case in stalled_cases]}
#     else:
#         return {"status": "no stalled cases"}































# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# import os
# from datetime import datetime, timezone
# from typing import List, Dict
# import time

# # Initialize FastAPI app
# router = APIRouter()

# # Define the Stall Timeout in hours
# STALL_TIMEOUT_HOURS = float(os.getenv("STALL_TIMEOUT_HOURS", "48"))

# # Define the case model
# class Case(BaseModel):
#     case_id: int
#     status: str
#     last_updated: str  # ISO format datetime string

# # Simple storage to simulate notifications (in-memory for now)
# notifications = []

# # Function to calculate hours since the last update
# def hours_since(last_updated: str) -> float:
#     last_dt = datetime.fromisoformat(last_updated)
#     now = datetime.now()
#     delta = now - last_dt
#     return delta.total_seconds() / 3600  # Return hours

# # Function to check for stalled cases and flag them as new notifications
# def check_stalled_cases(cases: List[Case]):
#     for case in cases:
#         idle_hours = hours_since(case.last_updated)
        
#         if idle_hours >= STALL_TIMEOUT_HOURS:
#             # Flag case as stalled and add it to notifications
#             notifications.append({
#                 "case_id": case.case_id,
#                 "message": f"Case {case.case_id} has been idle for more than {STALL_TIMEOUT_HOURS} hours.",
#                 "status": "new",  # Flag as new notification
#                 "timestamp": time.time()  # Use timestamp to track when the notification was created
#             })

# # API endpoint to check for stalled cases and return new notifications
# @router.post("/check_stalled_cases/")
# async def check_stalled_cases_api(cases: List[Case]):
#     check_stalled_cases(cases)
#     return {"status": "success", "notifications": notifications}

# # Endpoint to retrieve notifications (filtered by new status)
# @router.get("/notifications/")
# async def get_notifications():
#     # Filter only new notifications
#     new_notifications = [notif for notif in notifications if notif["status"] == "new"]
#     return {"notifications": new_notifications}

# # Endpoint to mark notifications as read
# @router.post("/mark_notifications_read/")
# async def mark_notifications_read():
#     for notif in notifications:
#         notif["status"] = "read"  # Mark all notifications as read
#     return {"status": "success", "message": "All notifications marked as read"}


























# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# import os
# from datetime import datetime, timezone
# from typing import List, Dict
# import time

# # Initialize FastAPI app
# router = APIRouter()

# # Define the Stall Timeout in hours
# STALL_TIMEOUT_HOURS = float(os.getenv("STALL_TIMEOUT_HOURS", "48"))

# # Define the case model
# class Case(BaseModel):
#     case_id: int
#     status: str
#     last_updated: str  # ISO format datetime string

# # Simple storage to simulate notifications (in-memory for now)
# notifications = []
# sent_notifications = set()  # Track which notifications have been sent

# # Function to calculate hours since the last update
# def hours_since(last_updated: str) -> float:
#     last_dt = datetime.fromisoformat(last_updated)
#     now = datetime.now()
#     delta = now - last_dt
#     return delta.total_seconds() / 3600  # Return hours

# # Function to check for stalled cases and flag them as new notifications
# def check_stalled_cases(cases: List[Case]):
#     for case in cases:
#         # Calculate idle hours
#         idle_hours = hours_since(case.last_updated)
        
#         # Check if the case is idle beyond the threshold
#         if idle_hours >= STALL_TIMEOUT_HOURS:
#             # Only add new notifications if the case hasn't been flagged before
#             if case.case_id not in sent_notifications:
#                 notifications.append({
#                     "case_id": case.case_id,
#                     "message": f"Case {case.case_id} has been idle for more than {STALL_TIMEOUT_HOURS} hours.",
#                     "status": "new",  # Flag as new notification
#                     "timestamp": time.time()  # Use timestamp to track when the notification was created
#                 })
#                 sent_notifications.add(case.case_id)  # Mark as processed to avoid duplication

# # API endpoint to check for stalled cases and return new notifications
# @router.post("/check_stalled_cases/")
# async def check_stalled_cases_api(cases: List[Case]):
#     check_stalled_cases(cases)  # Check for stalled cases and flag them as new notifications
#     return {"status": "success", "notifications": notifications}

# # Endpoint to retrieve notifications (filtered by new status)
# @router.get("/notifications/")
# async def get_notifications():
#     # Filter only new notifications
#     new_notifications = [notif for notif in notifications if notif["status"] == "new"]
#     return {"notifications": new_notifications}

# # Endpoint to mark notifications as read (when the user clicks on the bell)
# @router.post("/mark_notifications_read/")
# async def mark_notifications_read():
#     for notif in notifications:
#         notif["status"] = "read"  # Mark all notifications as read
#     return {"status": "success", "message": "All notifications marked as read"}












from fastapi import APIRouter, HTTPException
from typing import List, Dict
from app.mysql_ops import MysqlOps  # Ensure MysqlOps is correctly imported
from app.db import SessionLocal  # SessionLocal to manage DB connections
import time
import os

# Initialize FastAPI router
router = APIRouter()

# Define the Stall Timeout in hours
STALL_TIMEOUT_HOURS = float(os.getenv("STALL_TIMEOUT_HOURS", "48"))

# In-memory notifications storage (to be replaced with DB for production)
notifications = []
sent_notifications = set()  # Set to track already sent notifications

# Endpoint to check for stalled cases and send notifications for those that have been idle beyond the timeout
@router.post("/check_stalled_cases/")
async def check_stalled_cases_api():
    """
    Check for stalled cases and send notifications for those that have been idle beyond the timeout.
    """
    ops = MysqlOps()  # Initialize MysqlOps object to interact with DB
    
    # Fetch the stalled cases using the defined timeout threshold
    stalled_cases = ops.check_stalled_cases(STALL_TIMEOUT_HOURS)
    
    # Add new notifications for stalled cases that haven't been sent yet
    for case in stalled_cases:
        case_id = case["case_id"]
        # If notification for this case hasn't been sent before, add it
        if case_id not in sent_notifications:
            notifications.append(case)
            sent_notifications.add(case_id)  # Mark case as processed to avoid duplication

    return {"status": "success", "notifications": notifications}

# Endpoint to fetch all notifications (status: new)
@router.get("/notifications/")
async def get_notifications():
    """
    Fetch the list of new notifications (those that are marked as 'new').
    """
    # Filter the notifications that are marked as 'new'
    new_notifications = [notif for notif in notifications if notif["status"] == "new"]
    return {"notifications": new_notifications}

# Endpoint to mark all notifications as read
@router.post("/mark_notifications_read/")
async def mark_notifications_read():
    """
    Mark all notifications as read.
    """
    for notif in notifications:
        notif["status"] = "read"  # Mark all notifications as read after processing
    return {"status": "success", "message": "All notifications marked as read"}

# Helper function to ensure stalled cases are processed correctly
def check_and_process_stalled_cases(ops: MysqlOps):
    """
    Helper function to check for cases that have been idle for too long and process them.
    """
    # Fetch stalled cases from the database
    stalled_cases = ops.check_stalled_cases(STALL_TIMEOUT_HOURS)
    for case in stalled_cases:
        case_id = case["case_id"]
        # Avoid duplicate notifications for the same case
        if case_id not in sent_notifications:
            notifications.append(case)
            sent_notifications.add(case_id)  # Mark as processed

