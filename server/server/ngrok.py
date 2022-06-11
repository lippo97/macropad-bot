from pyngrok import ngrok

ngrok.set_auth_token('2AOhDlhgQOPhmNbcUOnkNC5gUcY_2NBtRRfDNa5YdYTa65ue5')
http_tunnel = ngrok.connect(5000, 'http')
print(http_tunnel)

ngrok_process = ngrok.get_ngrok_process()

try:
    ngrok_process.proc.wait()
except KeyboardInterrupt:
    print('shutting down')
    ngrok.kill()
