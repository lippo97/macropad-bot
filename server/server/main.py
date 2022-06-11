import pika
import logging


def create_connection():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='default')

    def callback(ch, method, properties, body):
        msg = body.decode('utf-8')
        print('received {}'.format(msg))

    channel.basic_consume(queue='default', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()
    logging.info('Channel start consuming messages.')

def main():
    create_connection()

if __name__ == '__main__':
    main()
