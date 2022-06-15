import sys
import os
import logging
import typer
import rabbitpy
import toml
from pynput import keyboard
from pynput.keyboard import Key, KeyCode

LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
logging.basicConfig(level=LOGLEVEL)

key_strings = {
    Key.f1: 'f1',
    Key.f2: 'f2',
    Key.f3: 'f3',
    Key.f4: 'f4',
    Key.f5: 'f5',
    Key.f6: 'f6',
    Key.f7: 'f7',
    Key.f8: 'f8',
    Key.f9: 'f9',
    Key.f10: 'f10',
    Key.f11: 'f11',
    Key.f12: 'f12',
}

def get_clip_for_key(key: Key, keybindings: dict[str, str]):
    if key in key_strings:
        key_str = key_strings[key]
        if key_str in keybindings:
            return keybindings[key_str]
    return None

def main(hostname: str, port: int):
    keybindings = toml.load('keys.toml')['keys']

    with rabbitpy.Connection(f'amqp://{hostname}:{port}') as conn:
        with conn.channel() as channel:
            default_exchange = rabbitpy.FanoutExchange(channel, 'default')
            default_exchange.declare()

            def send_msg(msg):
                logging.info(f'Sending message: {msg}')
                message = rabbitpy.Message(channel, msg)
                message.publish(exchange=default_exchange)

            def on_press(key):
                clip = get_clip_for_key(key, keybindings=keybindings)
                if clip is not None:
                    send_msg(f'play/{clip}')

            print('Client listening for keys...')
            try:
                with keyboard.Listener(on_press=on_press) as listener:
                    listener.join()
            except KeyboardInterrupt:
                print('Ctrl-C detected, attempting to close gracefully... ', end='')
                conn.close()
                print('Done.')

if __name__ == '__main__':
    typer.run(main)
