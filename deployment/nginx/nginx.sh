#!/bin/bash

CONFIG=~/nginx/conf/nginx.conf
PIDFILE=~/nginx/nginx.pid


# Do not change anything below unless you know what you do

DAEMON=/usr/local/nginx/sbin/nginx
NAME="nginx"
PATH=/sbin:/bin:/usr/sbin:/usr/bin
OPTS="-c $CONFIG -p $HOME/nginx/"

fail () {
    echo "failed!"
    exit 1
}

success () {
    echo "$NAME."
}

case "$1" in
  start)
      echo -n "Starting $NAME: "
      if start-stop-daemon --start --quiet --pidfile $PIDFILE --exec $DAEMON -- $OPTS ; then
        success
      else
        fail
      fi
    ;;
  stop)
      echo -n "Stopping $NAME: "
      if start-stop-daemon --stop --quiet --oknodo --retry 30 --pidfile $PIDFILE --exec $DAEMON ; then
        success
      else
        fail
      fi
    ;;
  reload)
      echo -n "Reloading $NAME configuration: "
      if ! eval "$DAEMON -t $OPTS" > /dev/null 2>&1; then
        eval "$DAEMON -t $OPTS"
        fail
      fi
      if start-stop-daemon --stop --signal 2 --oknodo --retry 30 --quiet --pidfile $PIDFILE --exec $DAEMON; then
        if start-stop-daemon --start --quiet --pidfile $PIDFILE --exec $DAEMON -- $OPTS ; then
          success
        else
          fail
        fi
      else
        fail
      fi
    ;;
  restart)
      $0 stop
      [ -r  $PIDFILE ] && while pidof nginx |\
          grep -q `cat $PIDFILE 2>/dev/null` 2>/dev/null ; do sleep 1; done
      $0 start
    ;;
  *)
      echo "Usage: $0 {start|stop|restart|reload}"
      exit 1
esac