# Temporary Snapshot Management

## Overview
Snapshots are now automatically deleted after 1 hour to prevent disk usage growth while still providing evidence for recent events.

## Configuration

Settings in `cv_pipeline/detect_track_fence.py`:

```python
SNAPSHOT_RETENTION_HOURS = 1       # Auto-delete after 1 hour
SNAPSHOT_CLEANUP_INTERVAL = 300    # Check every 5 minutes
```

## How It Works

1. **Snapshot Creation**
   - CV pipeline detects security event
   - Saves snapshot: `alert_{timestamp}_id{track_id}.jpg`
   - Stored in `snapshots/` folder

2. **Auto-Cleanup**
   - Every 5 minutes, check snapshot ages
   - Delete files older than 1 hour
   - Runs in background during CV processing

3. **Evidence Page**
   - Shows recent snapshots (last hour)
   - Older events show "snapshot not available"
   - Latest snapshot always available

## Benefits

✅ **Lower Disk Usage** - Snapshots auto-delete
✅ **Evidence Available** - Recent events have snapshots
✅ **No Manual Cleanup** - Automatic management
✅ **Configurable** - Adjust retention time as needed

## Customization

### Keep snapshots for 6 hours:
```python
SNAPSHOT_RETENTION_HOURS = 6
```

### Check for cleanup every 30 minutes:
```python
SNAPSHOT_CLEANUP_INTERVAL = 1800  # 30 minutes in seconds
```

### Disable cleanup (keep forever):
```python
SNAPSHOT_RETENTION_HOURS = 999999  # Effectively never delete
```

## Disk Usage Estimate

Assuming:
- 1 snapshot = ~50KB
- 10 events/hour = 500KB/hour
- 1 hour retention = ~500KB total

With cleanup, disk usage stays constant instead of growing indefinitely.
