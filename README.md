# Digital Marmot / Dima

This tool is a complete Python-based solution for building and deploying virtual machines, networks, and web apps in a home lab. It features a command line interface with history and a Tkinter GUI, offering over 65 commands.

It can configure and manage Git repositories, uWSGI servers, Nginx web servers, Let’s Encrypt SSL certificates, system services, Bind DNS servers, DHCP servers, SSH keys, GPG keys, PostgreSQL servers, nftables firewalls (with geo-blocking and port knocking), development, staging, and production environments, as well as preseed Debian virtual machines. Configurations are based on a custom templating system, with every setting carefully selected by me.

Websites are built on a custom web framework based on the WSGI application. They support multilingual content using a YAML-based CMS for managing static, blog, and gallery content.

The frontend of the websites uses a SCSS-based library for multimedia structure, spacing, color palettes, UI components, and animations.

Notes:
- Project was imported from [my Gitlab](https://gitlab.com/lucamatei).
- It's currently in the process of being updated and documented.
- Tokens and IPs found in the code are obsolete (I know it's bad practice).
