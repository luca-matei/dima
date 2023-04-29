
# dima

Description.  
Visit [lucamatei.eu/projects/dima](https://) for more.

## TO DO
- separate host, dev / test / prod machines, guest devices from main network in dhcp

## Prerequisites
Create a Gitlab REST API token from your [Gitlab profile](https://gitlab.com/-/profile/personal_access_tokens). Save it as you have to feed it later when it prompts.


## Installation

```
$ sudo apt install git
$ git clone https://gitlab.com/lucamatei/lm1.git
$ cd ./lm1    # Move to repository root
```

Non-sudo
```
$ su    # Change to root
# ./init    # Run init script with root priviledges
```

With sudo
```
$ sudo ./init
```

## Usage
Command line
```
$ dima <action> <object> <parameters>
```

Interactive
```
$ dima
> <action> <object> <parameters>

> q    # to quit
> h    # for help
```

GUI  
```
$ dima setup gui
```
Then visit [dima.example.com](https://) where "example.com" is your home domain.

## Permission system
dima belongs to [@lucamatei](https://gitlab.com/lucamatei) gitlab account.  
dima uses a REST API token from your gitlab account to save the projects.
