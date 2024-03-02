## k_amino
k_amino is unofficial client for [Aminoapps](https://aminoapps.com/) API in Python.

## Installation
You can use either `python3 setup.py install` or `pip3 install k-amino.py` to install. This module is tested on Python 3.8+.

## Contributing
k_amino is open source module, anyone can contribute. Please see the [Github Repository](https://github.com/Kwel999/k_amino)

## Discord
You can join the [Discord Server](https://discord.gg/wGRQYd3nVd) to add suggestions or to report problems
and to get new updates and changes

## Youtube Channel
you can check this [youtube channel](https://youtube.com/@KWELATEYOURPIZZA) for more information about script and bots

## Features
- Faster than other [Aminoapps](https://aminoapps.com/) python modules
- Supports async and sockets, events
- Easy and sample to use
- No `Too many requests.`
- Continual updates and bug fixes
- Have alot of useful functions

## Examples

#### Bot Support
```py
from k_amino import Client


client = Client(bot=True)
client.login("< email >", "< password >")


@client.command()
def test(data, ok: str = "ok"):
    data.subClient.send_message(data.chatId, f"Test is {ok}!")
```


#### Get SessionID
```py
import k_amino

client = k_amino.Client()
client.login("< email >", "< password >")
print(client.sid)
```

#### Login with SessionID
```py
import k_amino

client = k_amino.Client()
client.sid_login("< sid >")
print(client.sid)
```
#### Send a message in chat

```py
from k_amino import(
Client,
SubClient
)
import getpass

client = Client()
email = input("email:  ")
password = getpass.getpass("password:  ")
client.login(email=email, password=password)

chat_link = client.get_from_link(input("chat link:  "))
chat_id = chat_link.objectId
ndc_client = SubClient(comId=chat_link.comId)



while True:
    text = input("Your message: ")
    ndc_client.send_message(chatId=chat_id,message=text, messageType=0)
    print(f"message sended:  {text}")
```
