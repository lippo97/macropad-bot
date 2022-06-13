import sys
import os
import logging
import typer
import rabbitpy

from pynput import keyboard
from pynput.keyboard import Key

LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
logging.basicConfig(level=LOGLEVEL)

def main(hostname: str, port: int):
    with rabbitpy.Connection(f'amqp://{hostname}:{port}') as conn:
        with conn.channel() as channel:
            default_exchange = rabbitpy.FanoutExchange(channel, 'default')
            default_exchange.declare()

            def send_msg(msg):
                logging.info(f'Sending message: {msg}')
                message = rabbitpy.Message(channel, msg)
                message.publish(exchange=default_exchange)

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
                conn.close()
                print('Done.')

if __name__ == '__main__':
    typer.run(main)
