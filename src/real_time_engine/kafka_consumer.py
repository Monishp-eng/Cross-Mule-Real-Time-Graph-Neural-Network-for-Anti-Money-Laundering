"""
Kafka Consumer worker for real-time transaction processing.
Listens to live transaction events and processes them through the Orchestrator.
"""

import json
import logging
import os
import sys
import time

try:
    from kafka import KafkaConsumer
    from kafka.errors import NoBrokersAvailable
except ImportError:
    print("kafka-python is required to run the Kafka Consumer.")
    sys.exit(1)

from src.orchestrator import MuleDetectionOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run_consumer():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "live-transactions")
    group_id = os.getenv("KAFKA_GROUP_ID", "mule_detector_group")

    logger.info(f"Connecting to Kafka at {bootstrap_servers}, topic: {topic}")

    # Retry connection logic
    consumer = None
    for attempt in range(10):
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers.split(","),
                group_id=group_id,
                auto_offset_reset='latest',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logger.info("Successfully connected to Kafka.")
            break
        except NoBrokersAvailable:
            logger.warning(f"Kafka broker not available. Retrying in 5 seconds... (Attempt {attempt+1}/10)")
            time.sleep(5)
    
    if not consumer:
        logger.error("Failed to connect to Kafka. Exiting.")
        sys.exit(1)

    # Initialize Orchestrator
    orchestrator = MuleDetectionOrchestrator()
    logger.info("Mule Detection Orchestrator initialized. Waiting for events...")

    try:
        for message in consumer:
            raw_event = message.value
            logger.info(f"Received event: {raw_event.get('channel', 'UNKNOWN')} - {raw_event.get('event_id', 'no-id')}")
            
            try:
                # Wrap the event in the structure expected by Orchestrator
                if "channel" not in raw_event:
                    # Fallback wrapper if it's a raw payload
                    payload = {
                        "channel": "APP",
                        "raw_event": raw_event
                    }
                else:
                    payload = raw_event

                result = orchestrator.process_event(payload)
                
                status = result.get("status")
                decision = result.get("decision", "UNKNOWN")
                risk_score = result.get("risk_score", 0.0)
                
                if status == "SUCCESS":
                    logger.info(f"Processed successfully. Decision: {decision}, Risk Score: {risk_score:.4f}")
                else:
                    logger.error(f"Processing failed: {result.get('reason')}")
                    
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    except KeyboardInterrupt:
        logger.info("Shutting down consumer...")
    finally:
        consumer.close()
        logger.info("Consumer closed.")

if __name__ == "__main__":
    run_consumer()
