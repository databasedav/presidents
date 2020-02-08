import faust
import ssl

BOOTSTRAP_SERVER = "presidents.servicebus.windows.net:9093"
SECURITY_PROTOCOL = "SASL_SSL"
SASL_MECHANISM = "PLAIN"
SASL_USERNAME = "$ConnectionString"
SASL_PASSWORD = "Endpoint=sb://presidents.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=8Mkj0Ck8Ffw4NG4hntcZPMwkrQuaH2CLQMyyjmQqstE="

# p = aiokafka.AIOKafkaProducer(
#     loop=asyncio.get_running_loop(),
#     bootstrap_servers=BOOTSTRAP_SERVER,
#     client_id="hand_play_producer",
#     security_protocol=SECURITY_PROTOCOL,
#     sasl_mechanism=SASL_MECHANISM,
#     sasl_plain_username=SASL_PLAIN_USERNAME,
#     sasl_plain_password=SASL_PLAIN_PASSWORD,
#     ssl_context=context,
# )

import aiokafka.helpers

EVENTHUB_NAMESPACE = 'presidents'

ssl_context = ssl.create_default_context()

app = faust.App(
    'app',
    broker=f"kafka://{EVENTHUB_NAMESPACE}.servicebus.windows.net:9093",
    broker_credentials=faust.SASLCredentials(
        username=SASL_USERNAME,
        password=SASL_PASSWORD,
        ssl_context=aiokafka.helpers.create_ssl_context()
    ),
)

class Greeting(faust.Record):
    from_name: str
    to_name: str

@app.agent(value_type=Greeting)
async def hello(greetings):
    async for greeting in greetings:
        print(f'Hello from {greeting.from_name} to {greeting.to_name}')

@app.timer(interval=1.0)
async def example_sender(app):
    await hello.send(
        value=Greeting(from_name='Faust', to_name='you'),
    )

# if __name__ == '__main__':
#     hand_play_announcer.main()

# import asyncio
# import aiokafka
# import ssl
# from aiokafka.helpers import create_ssl_context
# import sys

# context = create_default_context()
# context.options &= ssl.OP_NO_TLSv1
# context.options &= ssl.OP_NO_TLSv1_1

# self.kafka = KafkaProducer(
#     bootstrap_servers=KAFKA_HOST,
#     connections_max_idle_ms=5400000,
#     security_protocol="SASL_SSL",
#     value_serializer=lambda v: json.dumps(v).encode("utf-8"),
#     sasl_mechanism="PLAIN",
#     sasl_plain_username="$ConnectionString",
#     sasl_plain_password={YOUR_KAFKA_ENDPOINT},
#     api_version=(0, 10),
#     retries=5,
#     ssl_context=context,
# )

# import certifi


# context = ssl.create_default_context()
# create_ssl_context(
#     # "./ca-certificates.crt"
#     cafile=certifi.where()
# )

# topic = "game_action_to_process"

# from confluent_kafka import Producer

# async def main():
#     p = aiokafka.AIOKafkaProducer(
#         loop=asyncio.get_running_loop(),
#         bootstrap_servers=BOOTSTRAP_SERVER,
#         client_id="hand_play_producer",
#         security_protocol=SECURITY_PROTOCOL,
#         sasl_mechanism=SASL_MECHANISM,
#         sasl_plain_username=SASL_PLAIN_USERNAME,
#         sasl_plain_password=SASL_PLAIN_PASSWORD,
#         ssl_context=context,
#     )
#     await p.start()
#     try:
#         await p.send_and_wait(topic, b"fuck")
#     finally:
#         await p.stop()


# if __name__ == "__main__":
#     asyncio.run(main())

    # conf = {
    #     "bootstrap.servers": BOOTSTRAP_SERVER,
    #     "security.protocol": "SASL_SSL",
    #     "ssl.ca.location": certifi.where(),#"./ca-certificates.crt",  # 
    #     "sasl.mechanism": SASL_MECHANISM,
    #     "sasl.username": SASL_PLAIN_USERNAME,
    #     "sasl.password": SASL_PLAIN_PASSWORD,
    #     "client.id": "python-example-producer",
    # }

    
    # # Create Producer instance
    # p = Producer(**conf)


    # def delivery_callback(err, msg):
    #     if err:
    #         sys.stderr.write('%% Message failed delivery: %s\n' % err)
    #     else:
    #         sys.stderr.write('%% Message delivered to %s [%d] @ %o\n' % (msg.topic(), msg.partition(), msg.offset()))


    # # Write 1-100 to topic
    # for i in range(0, 100):
    #     try:
    #         p.produce(topic, str(i), callback=delivery_callback)
    #     except BufferError as e:
    #         sys.stderr.write('%% Local producer queue is full (%d messages awaiting delivery): try again\n' % len(p))
    #     p.poll(0)

    # # Wait until all messages have been delivered
    # sys.stderr.write('%% Waiting for %d deliveries\n' % len(p))
    # p.flush()