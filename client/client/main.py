import sys
import pika
import os
import logging
import typer

from pynput import keyboard
from pynput.keyboard import Key

LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
logging.basicConfig(level=LOGLEVEL)

def main(hostname: str, port: int):
    connection = pika.BlockingConnection(pika.ConnectionParameters(hostname, port))
    channel = connection.channel()
    channel.exchange_declare(exchange='default',
                             exchange_type='fanout')
    def send_msg(msg):
        logging.info(f'Sending message: {msg}')
        channel.basic_publish(exchange='default',
                              routing_key='',
                              body=msg)

    def on_press(key):
        if key == Key.f8:
            send_msg('command/0')
        elif key == Key.f9:
            send_msg('command/1')
        elif key == Key.f10:
            send_msg('command/2')
        elif key == Key.f11:
            send_msg('command/3')

    print('Client listening for keys.')
    try:
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
    except KeyboardInterrupt:
        print('Ctrl-C detected, attempting to close gracefully... ', end='')
        connection.close()
        print('Done.')

if __name__ == '__main__':
    typer.run(main)
