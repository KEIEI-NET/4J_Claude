# Celery Parallel Processing Setup

This guide explains how to set up and use the Celery parallel processing infrastructure for the Graph Analyzer.

## Architecture

The parallel processing system consists of:

- **RabbitMQ**: Message broker for task distribution
- **Redis**: Result backend for storing task results
- **Neo4j**: Graph database for storing analysis results
- **Celery Workers**: Execute analysis tasks in parallel
- **Celery Beat**: Scheduler for periodic tasks
- **Flower**: Web-based monitoring tool (optional)

## Quick Start

### 1. Start Docker Services

Start all required services using Docker Compose:

```bash
docker-compose up -d
```

This will start:
- RabbitMQ (ports 5672, 15672)
- Redis (port 6379)
- Neo4j (ports 7474, 7687)
- Flower (port 5555)

Verify all services are healthy:

```bash
docker-compose ps
```

### 2. Start Celery Worker

In a separate terminal, start the Celery worker:

```bash
python scripts/start_worker.py
```

The worker will:
- Connect to RabbitMQ and Redis
- Listen to `analysis`, `graph`, and `default` queues
- Execute tasks with 4 concurrent workers
- Restart after processing 100 tasks

### 3. Start Celery Beat (Optional)

If you want to run periodic tasks (like cleanup), start Celery Beat:

```bash
python scripts/start_beat.py
```

### 4. Run Demo

Run the parallel processing demo:

```bash
python scripts/demo_parallel_analysis.py
```

This will demonstrate:
1. Single file analysis
2. Batch file analysis (parallel)
3. Analysis + graph update (chord pattern)
4. Task monitoring

## Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| RabbitMQ Management | http://localhost:15672 | guest / guest |
| Redis | localhost:6379 | (no auth) |
| Neo4j Browser | http://localhost:7474 | neo4j / password |
| Flower (Task Monitor) | http://localhost:5555 | (no auth) |

## Task Types

### 1. analyze_file

Analyze a single Java file.

```python
from src.graph_analyzer.worker.tasks import analyze_file

result = analyze_file.delay("/path/to/file.java", config={"enabled": True})
analysis_result = result.get(timeout=30)
```

### 2. batch_analyze_files

Analyze multiple files in parallel using `group()` pattern.

```python
from src.graph_analyzer.worker.tasks import batch_analyze_files

file_paths = ["file1.java", "file2.java", "file3.java"]
result = batch_analyze_files.delay(file_paths, config={"enabled": True})
batch_result = result.get(timeout=60)

print(f"Successful: {batch_result['successful']}/{batch_result['total_files']}")
```

### 3. update_graph

Update Neo4j graph with analysis results.

```python
from src.graph_analyzer.worker.tasks import update_graph

analysis_result = {
    "file": "UserService.java",
    "status": "success",
    "issues": [...]
}

result = update_graph.delay(
    analysis_result,
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)
graph_result = result.get(timeout=30)

print(f"Nodes created: {graph_result['nodes_created']}")
print(f"Relationships created: {graph_result['relationships_created']}")
```

### 4. batch_update_graph

Update graph with multiple analysis results.

```python
from src.graph_analyzer.worker.tasks import batch_update_graph

analysis_results = [
    {"file": "file1.java", "status": "success", "issues": []},
    {"file": "file2.java", "status": "success", "issues": []},
]

result = batch_update_graph.delay(
    analysis_results,
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)
```

### 5. analyze_and_update_graph (Chord Pattern)

Analyze files in parallel, then update graph when all analyses complete.

```python
from src.graph_analyzer.worker.tasks import analyze_and_update_graph

file_paths = ["file1.java", "file2.java", "file3.java"]

result = analyze_and_update_graph.delay(
    file_paths,
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
    config={"enabled": True}
)

chord_result = result.get(timeout=120)
print(f"Task ID: {chord_result['task_id']}")
print(f"Files processed: {chord_result['file_count']}")
```

### 6. cleanup_old_results (Periodic Task)

Automatically runs every 2 hours via Celery Beat.

```python
from src.graph_analyzer.worker.tasks import cleanup_old_results

result = cleanup_old_results.delay()
cleanup_result = result.get()
print(f"Cleaned: {cleanup_result['cleaned_count']} old results")
```

## Celery Configuration

### Task Queues

Tasks are routed to specific queues:

| Task | Queue | Purpose |
|------|-------|---------|
| analyze_file | analysis | File analysis tasks |
| batch_analyze_files | analysis | Batch analysis tasks |
| update_graph | graph | Graph update tasks |
| batch_update_graph | graph | Batch graph updates |
| cleanup_old_results | default | Periodic cleanup |

### Worker Settings

- **Prefetch Multiplier**: 1 (fetch one task at a time)
- **Max Tasks Per Child**: 100 (restart after 100 tasks)
- **Concurrency**: 4 (4 parallel workers)
- **Soft Time Limit**: 5 minutes
- **Hard Time Limit**: 10 minutes

### Retry Settings

- **Default Retry Delay**: 60 seconds
- **Max Retries**: 3
- **Result Expiration**: 1 hour

## Monitoring with Flower

Flower provides a web-based UI for monitoring Celery tasks:

1. Open http://localhost:5555
2. View:
   - Active tasks
   - Completed tasks
   - Worker status
   - Task execution time
   - Success/failure rates

## Performance Goals

| Metric | Target |
|--------|--------|
| Single file analysis | < 100ms |
| 10 files (parallel) | < 1 second |
| 100 files (parallel) | < 10 seconds |
| 35,000 files | < 2 hours |

## Troubleshooting

### Worker not connecting to RabbitMQ

```bash
# Check RabbitMQ is running
docker-compose ps rabbitmq

# Check RabbitMQ logs
docker-compose logs rabbitmq

# Verify environment variables
echo $CELERY_BROKER_URL
```

### Tasks not executing

```bash
# Check worker is running
# Should see: "celery@hostname ready"

# Check queue has tasks
# Open RabbitMQ management: http://localhost:15672
# Go to Queues tab

# Check Flower for task status
# Open: http://localhost:5555
```

### Neo4j connection errors

```bash
# Check Neo4j is running
docker-compose ps neo4j

# Verify credentials
docker-compose exec neo4j cypher-shell -u neo4j -p password

# Check Neo4j logs
docker-compose logs neo4j
```

## Stopping Services

Stop all Docker services:

```bash
docker-compose down
```

Stop and remove volumes (WARNING: deletes all data):

```bash
docker-compose down -v
```

## Development Tips

### Testing with Eager Mode

For unit tests, Celery can run tasks synchronously:

```python
from src.graph_analyzer.worker.celery_app import app

app.conf.task_always_eager = True
app.conf.task_eager_propagates = True

# Now tasks execute immediately in the same process
result = analyze_file.delay("/path/to/file.java")
# No need to wait, result is ready immediately
```

### Scaling Workers

Run multiple workers for better parallelism:

```bash
# Terminal 1
python scripts/start_worker.py

# Terminal 2
python scripts/start_worker.py

# Terminal 3
python scripts/start_worker.py
```

Or use multi-processing:

```bash
celery -A src.graph_analyzer.worker.celery_app worker \
  --loglevel=INFO \
  --concurrency=8 \
  --queues=analysis,graph,default
```

## Next Steps

1. Integrate Phase 1 file analysis logic into `analyze_file` task
2. Add integration tests with actual RabbitMQ/Redis
3. Implement distributed lock for concurrent graph updates
4. Add metrics collection (Prometheus/Grafana)
5. Optimize batch size for Neo4j bulk imports
