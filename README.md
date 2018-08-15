# AWS Elasticsearch Tools

## aws-es-restore.py

This is a tool for listing available snapshots made via the daily snapshot utility available
for hosted Elasticsearch domains.

### Usage

* `pip3 install -r requirements.txt`

* `aws-es-restore.py --list-snapshots --url [url]`: lists up to the last five available snapshots
and the indexes stored in them.

* `aws-es-restore.py --restore --snapshot [snapshot] --index [index_name] --url [url]`: restores a given index name from a snapshot. Can pass "all" to delete/restore all indexes, but note that AWS indicates there may be problems doing this due to permissions issues on the .kibana index. You can operate on multiple indexes by passing them as comma separated values, no spaces (the input is not presently sanitized).

### Examples

```
[ec2-user@ip-10-0-2-151 aws-elasticsearch-tools]$ ./aws-es-restore.py --list-snapshots --url https://vpc-tf-production-elasticsearch-otgkq7aqgi5k3oysldha6yledu.us-east-1.es.amazonaws.com

Elasticsearch cluster name: 065528155791:tf-production-elasticsearch, version: 6.2.3

Listing up to the latest five snapshots:
	Snapshot: 2018-08-14t23-13-35.676c6bfd-2660-4116-bc3a-f5294ad4f56d
	Indexes: events, users, places, .kibana, destination, user

	Snapshot: 2018-08-13t23-13-33.23f64c91-4960-4a4e-8ae6-1ba0b48582d4
	Indexes: events, places, .kibana, destination, users, user

	Snapshot: 2018-08-12t23-13-34.d95d8909-a304-4d1f-babd-81a95243eff2
	Indexes: events, places, .kibana, destination, users, user

	Snapshot: 2018-08-11t23-13-33.374dc2ab-f2d6-496d-8d2c-d4bdb6cc3bc8
	Indexes: events, places, .kibana, destination, users, user

	Snapshot: 2018-08-10t23-13-34.9380b608-06b5-4ad0-8b0e-7c7f7906c894
	Indexes: events, places, .kibana, destination, users, user
```

```
[ec2-user@ip-10-0-2-151 aws-elasticsearch-tools]$ ./aws-es-restore.py --url https://vpc-tf-production-elasticsearch-otgkq7aqgi5k3oysldha6yledu.us-east-1.es.amazonaws.com --snapshot-name 2018-08-14t23-13-35.676c6bfd-2660-4116-bc3a-f5294ad4f56d --index destination,events --restore

Elasticsearch cluster name: 065528155791:tf-production-elasticsearch, version: 6.2.3

WARNING: restoring an index necessitates the deletion of any existing index with the same name.
Proceed? (any key to continue, CTRL-C to abort)

Sending delete request for index destination,events.
Starting new HTTPS connection (1): vpc-tf-production-elasticsearch-otgkq7aqgi5k3oysldha6yledu.us-east-1.es.amazonaws.com
Delete index destination,events response status code: 200
Sleeping to allow index deletion before continuing.
Sending restore request for index destination,events from snapshot 2018-08-14t23-13-35.676c6bfd-2660-4116-bc3a-f5294ad4f56d.
Starting new HTTPS connection (1): vpc-tf-production-elasticsearch-otgkq7aqgi5k3oysldha6yledu.us-east-1.es.amazonaws.com
Restore index destination,events response status code: 200
```

