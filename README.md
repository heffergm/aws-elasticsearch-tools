# AWS Elasticsearch Tools

## aws-es-restore.py

This is a tool for listing available snapshots made via the daily snapshot utility available
for hosted Elasticsearch domains.

### Example usage and workflow:
* `aws-es-restore.py --list-snapshots --url [url]`: lists up to the last five available snapshots
and the indexes stored in them.
* `aws-es-restore.py --restore --snapshot [snapshot] --index [index_name] --url [url]`: restores a given index name from a snapshot. Can pass "all" to delete/restore all indexes, but note that AWS indicates there may be problems doing this due to permissions issues on the .kibana index.

