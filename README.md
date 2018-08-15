# AWS Elasticsearch Tools

## aws-es-restore.py

This is a tool for listing available snapshots made via the daily snapshot utility available
for hosted Elasticsearch domains.

### Example usage and workflow:
* `aws-es-restore.py --list-snapshots --url [url]`. 
* `aws-es-restore.py --restore --snapshot [snapshot] --index [index_name] --url [url]`

