import asyncio
from aio_pika import connect

async def on_message(message):
    print(message.body.decode('utf-8'))
    await asyncio.sleep(1)

async def main():
    connection = await connect("amqp://localhost/")
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue('default')

        await queue.consume(on_message)
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
