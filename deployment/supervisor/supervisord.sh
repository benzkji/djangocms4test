#!/bin/sh
### BEGIN INIT INFO
# Provides:
# Required-Start: $local_fs $syslog
# Required-Stop:  $local_fs $syslog
# Default-Start:  2 3 4 5
# Default-Stop:   0 1 6
# Short-Description: Gunicorn processes
### END INIT INFO


NAME="supervisord"
BASE_DIR="$HOME/supervisor"

PIDFILE="$BASE_DIR/$NAME.pid"
SOCKET="$BASE_DIR/$NAME.sock"
DAEMON=/usr/bin/supervisord
PATH=/sbin:/bin:/usr/sbin:/usr/bin
OPTS="-c $BASE_DIR/supervisord.conf"


status()
{
    UID=`id -u`
    if [ -s $PIDFILE ] && [ `pgrep -F $PIDFILE -U $UID` ]; then
        if [ $1 ]; then echo "$NAME is running"; fi
        return 0;
    else
        if [ $1 ]; then echo "$NAME is not running"; fi
        return 2;
    fi
}

start()
{
    if status; then echo "$NAME is running. Aborting."; return 3; fi
    printf "Starting $NAME "
    cd $BASE_DIR && $DAEMON $OPTS

    # Wait until the process is started
    x=0; while [ $x -lt 100 -a ! -s $PIDFILE ]; do x=`expr $x + 1`; printf "."; sleep .1; done

    # Because the process may crash after startup, wait 2 seconds before check the process status
    x=0; while [ $x -lt 20 ]; do x=`expr $x + 1`; printf "."; sleep .1; done

    if status; then echo "OK"; return 0; else echo "failed"; return 1; fi
}

stop()
{
    if [ -f $PIDFILE ]
    then
        PID=`cat $PIDFILE`
        kill -QUIT $PID;
        printf "Stopping $NAME "

        # Wait until the process has closed
        x=0; while [ $x -lt 100 -a `pgrep -P $PID -d ,` ]; do x=`expr $x + 1`; printf "."; sleep .1; done
        if [ `pgrep -P $PID -d ,` ]; then echo "failed"; else echo "OK"; fi
    else
        echo "Site $NAME is not running"
    fi
}

reload()
{
    if [ -f $PIDFILE ]
    then
        printf "Reloading $NAME: "
        kill -HUP `cat $PIDFILE` && echo "OK" || echo "failed";
    else
        echo "Site $NAME is not running"
    fi
}

update()
{
    local OLDPIDFILE="$PIDFILE.oldbin"
    if ! status; then echo "$NAME is not running. Aborting."; return 2; fi

    echo "Switch process for $NAME (`cat $PIDFILE`)"
    kill -s USR2 `cat $PIDFILE`

    # Wait until the new master proccess process has started
    x=0; while [ $x -lt 100 -a ! -f $OLDPIDFILE ]; do x=`expr $x + 1`; sleep .1; done

    if [ ! -f $OLDPIDFILE ]
    then
        echo "New master process not started. Aborting."
        return 1
    fi

    kill -s QUIT `cat $OLDPIDFILE`

    # Wait until the old process has closed
    x=0; while [ $x -lt 100 -a ! -f $PIDFILE ]; do x=`expr $x + 1`; sleep .1; done

    echo "New process running for $NAME (`cat $PIDFILE`)"
    return 0
}


case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop && start
        ;;
    reload)
        reload
        ;;
    status)
        status 1
        ;;
    update)
        update
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|reload|status|update}"
        RETVAL=1
esac
exit $RETVAL
