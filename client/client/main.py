import os
import logging
from typing import Optional
import typer
import rabbitpy
import toml
from pynput import keyboard
from pynput.keyboard import Key

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
            clip = keybindings[key_str]
            return clip if clip != "" else None
    return None

def main(hostname: str,
         port: int,
         username: Optional[str]=typer.Argument(None),
         password: Optional[str]=typer.Argument(None)):
    keybindings = toml.load('keys.toml')['keys']

    username = username or 'guest'
    password = password or 'guest'
    connection_string = f'amqp://{username}:{password}@{hostname}:{port}'

    with rabbitpy.Connection(connection_string) as conn:
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
