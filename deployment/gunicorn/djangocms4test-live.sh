#!/bin/sh
### BEGIN INIT INFO
# Provides:
# Required-Start: $local_fs $syslog
# Required-Stop:  $local_fs $syslog
# Default-Start:  2 3 4 5
# Default-Stop:   0 1 6
# Short-Description: Gunicorn processes
### END INIT INFO


# change site if you have multiple sites
PROJECT_ENV="live"
PROJECT_NAME="djangocms4test"
SITE="djangocms4test"

PROJECT_DIR="$HOME/sites/$PROJECT_NAME-$PROJECT_ENV"
WSGI="project.wsgi_${SITE}_${PROJECT_ENV}"
THE_ENV="$PROJECT_DIR/virtualenv"
# beware, choose the right version here! (2.7 for most mordern servers)
# PYTHONPATH="$THE_ENV/lib/python2.7/site-packages:$PROJECT_DIR"
PYTHONPATH="$THE_ENV/lib/python3.7/site-packages:$PROJECT_DIR"

# "--preload" - does prohibit kill -HUP!
PRELOAD=""
PIDFILE="$PROJECT_DIR/../$SITE-$PROJECT_ENV.pid"
SOCKET="$PROJECT_DIR/../$SITE-$PROJECT_ENV.sock"
DAEMON="$THE_ENV/bin/gunicorn"
PATH=/sbin:/bin:/usr/sbin:/usr/bin
WORKERS=2
OPTS="-D -b unix:///$SOCKET --worker-class gevent --workers $WORKERS --pid $PIDFILE $WSGI $PRELOAD"



start()
{
    printf "Starting $NAME "
    export PYTHONPATH=$PYTHONPATH;
    cd $PROJECT_DIR;
    $DAEMON $OPTS && echo "OK" || echo "failed";
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
        if [`pgrep -P $PID` ]; then echo "failed"; else echo "OK"; fi
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
    if [ ! -f $PIDFILE ]
    then
        echo "No process running. Aborting."
        return 1
    fi

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
    update)
        update
        ;;
    *)
        echo $"Usage: $0 {start|stop|restart|reload|update}"
        RETVAL=1
esac
exit $RETVA
