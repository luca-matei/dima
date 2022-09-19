
# Hal

Description.  
Visit [lucamatei.net/hal](https://) for more.

## Temp
```
$ git commit -am "Updated files"; git push
$ sudo -u hal git pull; sudo -u hal ./0.1/make; hal
```

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
$ hal <action> <object> <parameters>
```

Interactive
```
$ hal
> <action> <object> <parameters>

> q    # to quit
> h    # for help
```

GUI  
```
$ hal setup gui
```
Then visit [hal.example.com](https://) where "example.com" is your home domain.

## Permission system
Hal belongs to [@lucamatei](https://gitlab.com/lucamatei) gitlab account.  
Hal uses a REST API token from your gitlab account to save the projects.
