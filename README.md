Sample code taken from a project that is managing internal infrastructure / IoT devices, this part is VM specific.


Agg docker image: Fastapi/Asyncio/Pydantic

used to communicate with worker nodes, each VM server has both running, for HA purposes (in case one server is down for maintenance, traffic is directed to a different one that is available (nginx proxy handles LB)), as such as long as there is one VM server available, the API endpoint would be up and running, along with its workers.

Worker docker image: Fastapi/libvirt connection

used to communicate with libvirt with appropriate user via exposed unix socket. 


GET all example:

```
┌──[19:38:23](al💀srv01-beg01🖥️)[~]
└─# curl http://srv01.fsn01.digithrone.net:8081/v2/vms -s  | jq
[
  {
    "name": "llama",
    "uuid": "1a814f6f-f2ac-4918-8035-4382053c393a",
    "state": "off",
    "vcpus": 1,
    "memG": 128,
    "host": "srv01.beg01.digithrone.net",
    "FQDN": "llama.srv01.beg01.digithrone.net"
  },
  {
    "name": "veles",
    "uuid": "2685b8ba-8a65-4e87-9908-5c6f653278e0",
    "state": "running",
    "vcpus": 12,
    "memG": 32,
    "host": "srv01.beg01.digithrone.net",
    "FQDN": "veles.srv01.beg01.digithrone.net"
  },
  {
    "name": "doc01",
    "uuid": "3d4e6040-9bcd-4684-8f30-cf3260454c73",
    "state": "running",
    "vcpus": 12,
    "memG": 64,
    "host": "srv01.fsn01.digithrone.net",
    "FQDN": "doc01.srv01.fsn01.digithrone.net"
  },
  {
    "name": "vps01",
    "uuid": "b942420d-98a8-447d-8536-c79d9be6bb38",
    "state": "off",
    "vcpus": 6,
    "memG": 4,
    "host": "srv01.fsn01.digithrone.net",
    "FQDN": "vps01.srv01.fsn01.digithrone.net"
  }
]
```

Change state example:

```
┌──[19:45:26](al💀srv01-beg01🖥️)[~]
└─# curl -s -X POST "http://srv01.fsn01.digithrone.net:8081/v2/vms/doc01" -H "Content-Type: application/json" -d '{"state":"suspend"}'
[{"name":"doc01","uuid":"3d4e6040-9bcd-4684-8f30-cf3260454c73","state":"paused","vcpus":12,"memG":64,"host":"srv01.fsn01.digithrone.net","FQDN":"doc01.srv01.fsn01.digithrone.net"}]                                                                                                                                                                                                                    
┌──[19:45:32](al💀srv01-beg01🖥️)[~]
└─# curl -s -X POST "http://srv01.fsn01.digithrone.net:8081/v2/vms/doc01" -H "Content-Type: application/json" -d '{"state":"resume"}' 
[{"name":"doc01","uuid":"3d4e6040-9bcd-4684-8f30-cf3260454c73","state":"running","vcpus":12,"memG":64,"host":"srv01.fsn01.digithrone.net","FQDN":"doc01.srv01.fsn01.digithrone.net"}]  
```

.env example:

```
LIBVIRT_URI=qemu:///system
HOSTNAME=srv01.fsn01.digithrone.net
LIBVIRT_SSH_USER=root
LIBVIRT_SSH_PORT=22

WORKER_HOSTS=srv01.beg01.digithrone.net:8080,srv01.fsn01.digithrone.net:8080

#TODO - workaround for non-nixos HOSTS, per-host env
HOSTNAME=srv01.beg01.digithrone.net
```
