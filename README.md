## KAmino
KAmino is unofficial client for [Aminoapps](https://aminoapps.com/) API in Python. 

## Installation
You can use either `python3 setup.py install` or `pip3 install kamino` to install. This module is tested on Python 3.9+.

## Contributing
KAmino is open source module, anyone can contribute. Please see the [Github Repository](https://github.com/Kwel999/KAmino)

## Discord
You can join the [Discord Server](https://discord.gg/vhBtt2QB) to add suggestions or to report problems
and to get new updates and changes

## Features
- Faster than other [Aminoapps](https://aminoapps.com/) python modules
- Supports async and sockets, events
- Easy and sample to use
- No `Too many requests.`
- Continual updates and bug fixes
- Have alot of useful functions

## Examples
#### Get SessionID
```py
import kamino

client = kamino.Client()
client.login("< email >", "< password >")
print(client.sid)
```
#### Login with SessionID
```py
import kamino

client = samino.Client()
client.sid_login("< sid >")
print(client.sid)
```
#### Send a message in chat
```py
import kamino

client = kamino.Client()
client.login("< email >", "< password >")
path = client.get_from_link("< chat link >")
local = kamino.Local(path.comId)
local.send_message(path.objectId, "< message >")
```
# KAmino
