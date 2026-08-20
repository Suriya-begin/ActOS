#!/bin/bash
# Create Kafka topics for ActOS event bus
kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 3 --topic actos.commands
kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 3 --topic actos.results
kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 3 --topic actos.events
kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic actos.voice.stream
kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic actos.agent.status
echo "✓ All Kafka topics created"
