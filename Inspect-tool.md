# Foxhole Inspector Documentation

The Foxhole Inspector is a diagnostic tool that provides detailed information about your deployment's state, including database statistics, Redis status, MinIO storage, and filesystem information.

## Prerequisites

- Docker and Docker Compose must be running
- The Foxhole application must be deployed and running
- You must run the script from the project root directory

## Usage

```bash
./inspect.sh [options]
```

### Options

- `--format <format>`: Output format (default: json)
  - `json`: Output in JSON format
  - `text`: Output in human-readable text format
- `--user-secret <secret>`: Filter inspection by specific user secret
- `--hours <n>`: Show recent activity for the last n hours (default: 24)
- `--output <file>`: Write output to a file instead of stdout

### Examples

1. View help and available options:
```bash
./inspect.sh --help
```

2. Basic inspection in text format:
```bash
./inspect.sh --format text
```

3. Inspect specific user's data:
```bash
./inspect.sh --user-secret "user-secret-here" --format text
```

4. Custom time range inspection:
```bash
./inspect.sh --hours 48 --format text
```

5. Save inspection results to file:
```bash
./inspect.sh --format json --output inspection_results.json
```

## Output Information

The inspector provides information about:

### Database Status
- Database file size
- Table schemas
- Entity counts (users, tasks, topics, people, notes)
- Recent activity

### Redis Status
- Connection status
- Memory usage
- Total keys
- Sample of stored keys

### MinIO Status
- Connection status
- Bucket information
- Recent objects

### Filesystem Status
- Data directory size
- Directory contents
- Path information

## Troubleshooting

If you encounter any issues:

1. Ensure the application containers are running:
```bash
docker-compose ps
```

2. Check container logs:
```bash
docker-compose logs app
```

3. Verify database path:
```bash
./inspect.sh --format text | grep "database"
```

## Notes

- The inspection is non-intrusive and read-only
- Large datasets might take longer to process
- Memory usage might spike temporarily during inspection
- All timestamps are in ISO format
- File sizes are in bytes unless otherwise specified
