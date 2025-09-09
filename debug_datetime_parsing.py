#!/usr/bin/env python3

from datetime import datetime

# Test the exact datetime parsing that happens in the router
now = datetime.now()
print(f"Original datetime: {now}")

# This is what my test sends
iso_string = now.isoformat()
print(f"ISO string sent: {iso_string}")

# This is what the router does
parsed_dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
print(f"Parsed datetime: {parsed_dt}")

# This is what the prediction service does  
service_dt = datetime.now()
print(f"Service datetime: {service_dt}")

print(f"\nTime differences:")
print(f"Original vs Parsed: {(parsed_dt - now).total_seconds()} seconds")
print(f"Original vs Service: {(service_dt - now).total_seconds()} seconds")

# Check if there are any timezone issues
print(f"\nTimezone info:")
print(f"Original timezone: {now.tzinfo}")
print(f"Parsed timezone: {parsed_dt.tzinfo}")
print(f"Service timezone: {service_dt.tzinfo}")

# The router only uses the hour
print(f"\nHour extraction:")
print(f"Parsed hour: {parsed_dt.hour}")
print(f"Service hour: {service_dt.hour}")
