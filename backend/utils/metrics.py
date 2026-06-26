from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
import time

SCRAPES_TOTAL = Counter("scrapes_total", "Total scrapes", ["source", "status"])
LISTINGS_FOUND = Counter("listings_found_total", "Listings found per source", ["source"])
ANALYSIS_SCORE = Gauge("analysis_score", "Car analysis scores")
SCRAPE_DURATION = Histogram("scrape_duration_seconds", "Scrape duration", ["source"])
API_REQUESTS = Counter("api_requests_total", "API requests", ["method", "endpoint"])
API_DURATION = Histogram("api_duration_seconds", "API request duration", ["method", "endpoint"])
CARS_ACTIVE = Gauge("cars_active_total", "Active car listings")
NOTIFICATIONS_SENT = Counter("notifications_sent_total", "Notifications sent", ["channel"])


async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response: Response = await call_next(request)
    duration = time.time() - start
    API_REQUESTS.labels(method=request.method, endpoint=request.url.path).inc()
    API_DURATION.labels(method=request.method, endpoint=request.url.path).observe(duration)
    return response
