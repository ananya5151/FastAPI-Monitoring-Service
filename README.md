# FastAPI Monitoring Service

This project demonstrates a complete observability stack for a FastAPI service using Prometheus, Grafana, and Jaeger. It is designed for technical evaluation and showcases production-ready monitoring patterns.

## Features

- **FastAPI** app with multiple endpoints: `/`, `/slow`, `/error`, `/health`, `/cpu-intensive`
- **Prometheus** for metrics collection
- **Grafana** for dashboards and visualization
- **Jaeger** for distributed tracing
- **Loki** (optional) for log aggregation
- **Traffic generator** script to simulate real-world load

## Quick Start

1. **Clone the repo:**

   ```sh
   git clone https://github.com/ananya5151/FastAPI-Monitoring-Service.git
   cd FastAPI-Monitoring-Service
   ```

2. **Start all services:**

   ```sh
   docker-compose up -d
   ```

3. **Run the traffic generator:**

   ```sh
   python traffic_generator.py
   ```

4. **Access dashboards:**
   - Grafana: [http://localhost:3000](http://localhost:3000) (admin/admin)
   - Prometheus: [http://localhost:9090](http://localhost:9090)
   - Jaeger: [http://localhost:16686](http://localhost:16686)

## PromQL Example Queries

- **Request rate:**

  ```
  rate(http_requests_total[5m])
  ```

- **Average latency:**

  ```
  rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
  ```

- **Error rate:**

  ```
  rate(http_requests_total{status_code=~"4..|5.."}[5m])
  ```

- **Request count by endpoint:**

  ```
  sum by (endpoint) (http_requests_total)
  ```

## Endpoints

- `/` - Fast response
- `/slow` - Slow response (1-3s)
- `/error` - Fails ~70% of the time
- `/health` - Health check
- `/cpu-intensive` - Simulates CPU load

## Recording Script Outline

1. Start the stack: `docker-compose up -d`
2. Show FastAPI docs: `http://localhost:8000/docs`
3. Run traffic generator: `python traffic_generator.py`
4. Show Grafana dashboards (metrics/logs)
5. Show Jaeger traces
6. Briefly explain the setup

## License

MIT
