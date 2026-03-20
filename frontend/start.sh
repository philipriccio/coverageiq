#!/bin/sh
cp /usr/share/nginx/html/nginx.conf /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
