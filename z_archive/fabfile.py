# flake8: noqa
import datetime
import os
import sys

from fabric.api import task, run, settings, roles, cd, execute, hide, puts
from fabric.contrib.console import confirm
from fabric.operations import get, local, put
from fabric.contrib.project import rsync_project
from fabric.contrib import django

from fabconf import env, stage, live  # noqa
from fabconf import upgrade_glitchtip, custom_bootstrap

# hm. https://github.com/fabric/fabric/issues/256
sys.path.insert(0, sys.path[0])

# set some basic things, that are just needed.
env.forward_agent = True

# check for some defaults to be set?
# in a method, to be called after each setup? ie at the end of stage/live?
# def check_setup():
#     if not getattr(env, 'project_name'):
#         exit("env.project_name must be set!")
# project_name
# repository
# sites
# is_postgresql
# is_nginx_gunicorn
# needs_main_nginx_files
# is_uwsgi
# remote_ref
# requirements_files
# requirements_file
# is_python3
# deploy_crontab
# roledefs
# project_dir = '/home/{main_user}/sites/{project_name}-{env_prefix}'.format(**env)
# virtualenv_dir = '{project_dir}/virtualenv'.format(**env)
# gunicorn_restart_command = '~/init/{site_name}.{env_prefix}.sh restart'
# nginx_restart_command = '~/init/nginx.sh restart'
# uwsgi_restart_command = 'touch $HOME/uwsgi.d/{site_name}.{env_prefix}.ini'
# project_conf = 'project.settings._{project_name}_{env_prefix}'.format(**env)


# ==============================================================================
# Actual tasks
# ==============================================================================


@task
@roles("web", "db")
def create_virtualenv(force=False):
    """
    Bootstrap the environment.
    """
    with hide("running", "stdout"):
        exists = run('if [ -d "{virtualenv_dir}" ]; then echo 1; fi'.format(**env))
    if exists:
        if not force:
            puts(
                "Assuming virtualenv {virtualenv_dir} has already been created "
                "since this directory exists."
                "If you need, you can force a recreation.".format(**env)
            )
            return
        else:
            run("rm -rf {virtualenv_dir}".format(**env))
    venv_command = "virtualenv {virtualenv_dir} ".format(**env)
    if getattr(env, "is_python3", None):
        venv_command += " --python=python3"
    run(venv_command)
    requirements()
    puts("Created virtualenv at {virtualenv_dir}.".format(**env))


@task
@roles("web", "db")
def clone_repos():
    """
    clone the repository.
    """
    with hide("running", "stdout"):
        exists = run('if [ -d "{project_dir}" ]; then echo 1; fi'.format(**env))
    if exists:
        puts(
            "Assuming {repository} has already been cloned since "
            "{project_dir} exists.".format(**env)
        )
        return
    run("git clone {repository} {project_dir}".format(**env))
    puts("cloned {repository} to {project_dir}.".format(**env))


@task
@roles("web", "db")
def create_database():
    # this will fail straight if the database already exists.
    if env.is_postgresql:
        puts("PostgreSQL db must be created manually.")
    else:
        create_mycnf()
        my_cnf_file = _get_my_cnf_name()
        settings = _get_settings()
        db_settings = settings.DATABASES
        run(
            'echo "CREATE DATABASE {dbname} CHARACTER SET utf8 COLLATE utf8_unicode_ci;'
            '" | mysql --defaults-file={cnf_file} '.format(
                dbname=db_settings["default"]["NAME"],
                cnf_file=my_cnf_file,
            )
        )


@task
@roles("web", "db")
def bootstrap():
    clone_repos()
    create_nginx_folders()
    create_supervisor_folders()
    create_virtualenv()
    create_database()
    puts(
        "Bootstrapped {project_name} on {host} (cloned repos, created venv and db).".format(
            **env
        )
    )


@task
@roles("web", "db")
def create_supervisor_folders():
    if getattr(env, "is_supervisord", None):
        run("mkdir --parents ~/supervisor/programs")
        run("mkdir --parents ~/supervisor/logs")


@task
@roles("web", "db")
def create_nginx_folders():
    """
    do it.
    """
    if getattr(env, "needs_main_nginx_files", None):
        with hide("running", "stdout"):
            exists = run('if [ -d "~/nginx" ]; then echo 1; fi')
        if exists:
            puts("nginx dir already exists. manual action needed, if really...")
            return
        run("mkdir ~/nginx")
        run("mkdir ~/nginx/conf")
        run("mkdir ~/nginx/conf/sites")
        run("mkdir ~/nginx/temp")
        run("mkdir ~/nginx/logs")
        run("mkdir ~/nginx/logs/archive")
        puts("created ~/nginx & co.".format(**env))
    else:
        puts('no nginx files created, check "needs_main_nginx_files" in env.')


@task
def deploy(verbosity="noisy"):
    """
    Full server deploy.
    Updates the repository (server-side), synchronizes the database, collects
    static files and then restarts the web service.
    """
    if verbosity == "noisy":
        hide_args = []
    else:
        hide_args = ["running", "stdout"]
    with hide(*hide_args):
        puts("Updating repository...")
        execute(update)
        puts("Collecting static files...")
        execute(collectstatic)
        puts("Synchronizing database...")
        execute(migrate)
        puts("Restarting web server...")
        execute(restart)
        puts("Installing crontab...")
        execute(crontab)


@task
@roles("web")
def git_set_remote():
    """
    reset the repository's remote.
    """
    with cd(env.project_dir):
        remote, dest_branch = env.remote_ref.split("/", 1)
        run("git remote remove {}".format(remote))
        run("git remote add {} {}".format(remote, env.repository))
        run("git fetch {}".format(remote))
        run("git branch --set-upstream-to={} {}".format(env.remote_ref, dest_branch))


@task
@roles("web", "db")
def update(action="check", tag=None):
    """
    Update the repository (server-side).

    By default, if the requirements file changed in the repository then the
    requirements will be updated. Use ``action='force'`` to force
    updating requirements. Anything else other than ``'check'`` will avoid
    updating requirements at all.
    """
    with cd(env.project_dir):
        remote, dest_branch = env.remote_ref.split("/", 1)
        run("git fetch {remote}".format(remote=remote, dest_branch=dest_branch, **env))
        with hide("running", "stdout"):
            changed_files = run(
                "git diff-index --cached --name-only " "{remote_ref}".format(**env)
            ).splitlines()
        if not changed_files and action != "force":
            # No changes, we can exit now.
            return
        reqs_changed = False
        if action == "check":
            for file in env.requirements_files:
                if file in changed_files:
                    reqs_changed = True
                    break
        # before. run('git merge {remote_ref}'.format(**env))
        if tag:
            run("git checkout tags/{tag}".format(tag=tag, **env))
        else:
            run("git checkout {dest_branch}".format(dest_branch=dest_branch, **env))
            run("git pull".format(dest_branch=dest_branch, **env))
        run('find -name "*.pyc" -delete')
        run("git clean -df")
        # run('git clean -df {project_name} docs requirements public/static '.format(**env))
        # fix_permissions()
    if action == "force" or reqs_changed:
        # Not using execute() because we don't want to run multiple times for
        # each role (since this task gets run per role).
        requirements()
    if getattr(env, "env_file", None):
        remote_path = os.path.join(
            env.project_dir, "envs", ".env-{env_prefix}".format(**env)
        )
        put(local_path="envs/.env-{env_prefix}".format(**env), remote_path=remote_path)


@task
@roles("web")
def crontab():
    """
    install crontab
    """
    if env.deploy_crontab:
        if getattr(env, "contab_file", None):
            crontab_file = env.crontab_file
        else:
            crontab_file = "deployment/crontab.txt"
        with cd(env.project_dir):
            run("crontab {}".format(crontab_file))
    else:
        puts("not deploying crontab to %s!" % env.env_prefix)


@task
@roles("web")
def copy_restart_supervisord():
    """
    install and restart supervisord
    """
    if env.get("is_supervisord", None):
        run("mkdir --parents ~/supervisor/programs")
        run("mkdir --parents ~/supervisor/logs")
        run(
            "cp {project_dir}/deployment/supervisor/supervisord.conf"
            " ~/supervisor/.".format(**env)
        )
        run(
            "cp {project_dir}/deployment/supervisor/supervisord.sh"
            " ~/init/.".format(**env)
        )
        run("chmod u+x $HOME/init/supervisord.sh")

        # programs
        run("rm -f ~/supervisor/programs/*-{env_prefix}".format(**env))
        run(
            "cp {project_dir}/deployment/supervisor/programs/*-{env_prefix}"
            " ~/supervisor/programs/.".format(**env)
        )

        # restart
        run("~/init/supervisord.sh restart")
        # run('supervisorctl -c ~/supervisor/supervisord.conf update')
        run("supervisorctl -c ~/supervisor/supervisord.conf status")
    else:
        puts("not deploying supervisord to %s!" % env.env_prefix)


@task
@roles("web")
def supervisorctl(command):
    """
    control supervisord
    """
    if env.get("is_supervisord", None):
        run("supervisorctl -c ~/supervisor/supervisord.conf {}".format(command))
    else:
        puts("supervisord not deployed to %s!" % env.env_prefix)


@task
@roles("web")
def build_put_webpack():
    """
    build webpack, put on server!
    """
    local_branch = local("git branch --show-current")
    if not env.remote_ref.endswith(local_branch):
        yes_no = confirm(
            "Configured remote_ref for {} is {}, but you are on branch {}. Continue anyway (y/N)?",
            default=False,
        )
        if not yes_no:
            exit(0)
    local("yarn build")
    base_static_path = "apps/{project_name}/static/{project_name}/".format(**env)
    local_path = "{}bundle".format(base_static_path)
    remote_path = "{}/{}.".format(env.project_dir, base_static_path)
    run("mkdir --parent {}".format(remote_path))
    put(local_path=local_path, remote_path=remote_path)


@task
@roles("web")
def collectstatic():
    """
    Collect static files from apps and other locations in a single location.
    """
    dj("collectstatic --link --noinput")


@task
@roles("db")
def migrate(sync=True, migrate=True):
    """
    Synchronize the database.
    """
    dj("migrate --noinput")
    # needed when using django-modeltranslation
    # with third party apps
    # make it configurable?!
    # dj('sync_translation_fields')


@task
@roles("db")
def createsuperuser():
    """
    Create super user.
    """
    dj("createsuperuser")


@task
@roles("web")
def restart():
    """
    Copy gunicorn & nginx config, restart them.
    """
    if env.is_nginx_gunicorn:
        if not getattr(env, "is_supervisord", None):
            copy_restart_gunicorn()
        copy_restart_nginx()
    if env.is_uwsgi:
        copy_restart_uwsgi()
    if env.is_apache:
        exit("apache restart not implemented!")
    if env.get("is_supervisord", None):
        copy_restart_supervisord()
    if env.get("is_systemd", None):
        exit("global systemd restart not implemented!")


@task
@roles("web")
def stop_django():
    """
    stop django, for now, may be restarted...
    """
    if env.is_nginx_gunicorn:
        stop_gunicorn()
    if env.is_uwsgi:
        exit("uswgi stop not implemented!")
        stop_uwsgi()
    if env.is_apache:
        exit("apache stop not implemented!")


def stop_gunicorn():
    for site in env.sites:
        run(env.gunicorn_stop_command.format(site=site, **env))


@task
@roles("web")
def disable_django():
    """
    disable django service/app completely
    """
    if env.is_nginx_gunicorn:
        disable_gunicorn()
    if env.is_uwsgi:
        exit("uswgi disable not implemented!")
        disable_uwsgi()
    if env.is_apache:
        exit("apache disable not implemented!")


def disable_gunicorn():
    stop_gunicorn()
    for site in env.sites:
        run("rm $HOME/init/{site}-{env_prefix}.sh".format(site=site, **env))


def copy_restart_gunicorn():
    for site in env.sites:
        run(
            "cp {project_dir}/deployment/gunicorn/{site}-{env_prefix}.sh"
            " $HOME/init/.".format(site=site, **env)
        )
        run("chmod u+x $HOME/init/{site}-{env_prefix}.sh".format(site=site, **env))
        if not env.get("is_supervisord", None) and not env.get("is_systemd", None):
            run(env.gunicorn_restart_command.format(site=site, **env))


def copy_restart_nginx():
    for site in env.sites:
        run(
            "cp {project_dir}/deployment/nginx/{site}-{env_prefix}.txt"
            " $HOME/nginx/conf/sites/.".format(site=site, **env)
        )
    # nginx main, may be optional!
    if env.needs_main_nginx_files:
        run(
            "cp {project_dir}/deployment/nginx/logrotate.conf"
            " $HOME/nginx/conf/.".format(**env)
        )
        run(
            "cp {project_dir}/deployment/nginx/nginx.conf"
            " $HOME/nginx/conf/.".format(**env)
        )
        if not getattr(env, "is_supervisord", None):
            run("cp {project_dir}/deployment/nginx/nginx.sh $HOME/init/.".format(**env))
            run("chmod u+x $HOME/init/nginx.sh")
    if not getattr(env, "is_supervisord", None):
        run(env.nginx_restart_command)
    else:
        run(
            "cp {project_dir}/deployment/supervisor/programs/nginx"
            " $HOME/supervisor/programs/.".format(**env)
        )


def copy_restart_uwsgi():
    for site in env.sites:
        run(
            "cp {project_dir}/deployment/uwsgi/{site}-{env_prefix}.ini"
            " $HOME/uwsgi.d/.".format(site=site, **env)
        )
        # cp does the touch already!
        # run(env.uwsgi_restart_command.format(site=site, **env))


@task
@roles("web", "db")
def requirements():
    """
    Update the requirements.
    """
    # let it get some more older
    # virtualenv('pip-sync {project_dir}/{requirements_file}'.format(**env))
    virtualenv("pip install -r {project_dir}/{requirements_file}".format(**env))


@task
@roles("web")
def get_version():
    """
    Get installed version from each server.
    """
    with cd(env.project_dir):
        run("git describe --tags")
        run("git log --graph --pretty=oneline -n20")


@task
@roles("db")
def get_db(dump_only=False):
    local_db_name = _get_local_db_name()
    remote_db_name = _get_remote_db_name()
    if env.is_postgresql:
        get_db_postgresql(
            local_db_name,
            remote_db_name,
            dump_only,
        )
    else:
        get_db_mysql(
            local_db_name,
            remote_db_name,
            dump_only,
        )


@task
@roles("db")
def put_db(local_db_name=False, from_file=None):
    yes_no1 = confirm(
        "This will erase your remote DB! Continue?",
        default=False,
    )
    if not yes_no1:
        return
    yes_no2 = confirm("Are you sure?", default=False)
    if not yes_no2:
        return

    remote_db_name = _get_remote_db_name()
    if not local_db_name:
        local_db_name = _get_local_db_name()
    # go for it!
    if env.is_postgresql:
        put_db_postgresql(local_db_name, from_file, remote_db_name)
    else:
        put_db_mysql(local_db_name, from_file, remote_db_name)


def get_db_mysql(local_db_name, remote_db_name, dump_only=False):
    """
    dump db on server, import to local mysql (must exist)
    """
    create_mycnf()
    my_cnf_file = _get_my_cnf_name()
    date = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    dump_name = "dump_%s_%s-%s.sql" % (env.project_name, env.env_prefix, date)
    remote_dump_file = os.path.join(env.project_dir, dump_name)
    local_dump_file = "./%s" % dump_name
    run(
        "mysqldump"
        # for pg conversion!
        # ' --compatible=postgresql'
        # ' --default-character-set=utf8'
        " --defaults-file={cnf_file}"
        " {database} > {file}".format(
            cnf_file=my_cnf_file, database=remote_db_name, file=remote_dump_file, **env
        )
    )
    get(remote_path=remote_dump_file, local_path=local_dump_file)
    run("rm %s" % remote_dump_file)
    if not dump_only:
        local("mysql -u root %s < %s" % (local_db_name, local_dump_file))
        local("rm %s" % local_dump_file)


def put_db_mysql(local_db_name, from_file, remote_db_name):
    """
    dump local db, import on server database (must exist)
    """
    create_mycnf()
    my_cnf_file = _get_my_cnf_name()
    if not from_file:
        dump_name = "dump_for_%s.sql" % env.env_prefix
        local_dump_file = "./%s" % dump_name
        local(
            "mysqldump --user=root {database} > {file}".format(
                database=local_db_name,
                file=local_dump_file,
            )
        )
    else:
        dump_name = os.path.basename(from_file)
        local_dump_file = from_file
    remote_dump_file = os.path.join(env.project_dir, dump_name)
    put(remote_path=remote_dump_file, local_path=local_dump_file)
    if not from_file:
        local("rm %s" % local_dump_file)
    run(
        "mysql  "
        " --defaults-file={cnf_file}"
        " {database} < {file} ".format(
            cnf_file=my_cnf_file, database=remote_db_name, file=remote_dump_file, **env
        )
    )
    run("rm %s" % remote_dump_file)


@task
@roles("db")
def create_mycnf(force=False):
    my_cnf_file = _get_my_cnf_name()
    with hide("running", "stdout"):
        exists = run(
            'if [ -f "{cnf_file}" ]; then echo 1; fi'.format(
                cnf_file=my_cnf_file, **env
            )
        )
    if force or not exists:
        settings = _get_settings()
        db_settings = settings.DATABASES
        if exists:
            run("rm {cnf_file}".format(cnf_file=my_cnf_file, **env))
        local('echo "[client]" >> {cnf_file}'.format(cnf_file=my_cnf_file, **env))
        local(
            'echo "# The following password will be sent to all'
            'standard MySQL clients" >> {cnf_file}'.format(cnf_file=my_cnf_file, **env)
        )
        local(
            'echo "password = "{pw}"" >> {cnf_file}'.format(
                cnf_file=my_cnf_file, pw=db_settings["default"]["PASSWORD"], **env
            )
        )
        local(
            'echo "user = "{db_user}"" >> {cnf_file}'.format(
                cnf_file=my_cnf_file, db_user=db_settings["default"]["USER"], **env
            )
        )
        put("{cnf_file}".format(cnf_file=my_cnf_file))
        local("rm {cnf_file}".format(cnf_file=my_cnf_file, **env))


def _get_postgres_options_prompts(remote_db_options):
    options = ""
    user = remote_db_options.get("USER", "")
    if user:
        options += " --username={}".format(user)
    if remote_db_options.get("HOST", None):
        options += " --host={}".format(remote_db_options["HOST"])
    prompts = {}
    if remote_db_options.get("PASSWORD", None):
        options += " --password"
        prompts = {
            "Password: ": remote_db_options["PASSWORD"],
            "Password for user {}: ".format(user): remote_db_options["PASSWORD"],
        }
    return options, prompts


def get_db_postgresql(local_db_name, remote_db_name, dump_only=False):
    """
    dump db on server, import to local mysql (must exist)
    """
    date = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    dump_name = "dump_%s_%s-%s.sql" % (env.project_name, env.env_prefix, date)
    remote_dump_file = os.path.join(env.project_dir, dump_name)
    local_dump_file = "./%s" % dump_name
    django_settings = _get_settings()
    remote_db_settings = django_settings.DATABASES.get("default", None)
    options, prompts = _get_postgres_options_prompts(remote_db_settings)
    with settings(prompts=prompts):
        run(
            "pg_dump {options} --clean --no-owner --if-exists --schema=public {database} > {file}".format(
                options=options,
                database=remote_db_settings["NAME"],
                file=remote_dump_file,
            )
        )
    get(remote_path=remote_dump_file, local_path=local_dump_file)
    run("rm %s" % remote_dump_file)
    if not dump_only:
        # local('dropdb %s_dev' % env.project_name)
        # local('createdb %s_dev' % env.project_name)
        local("psql %s < %s" % (local_db_name, local_dump_file))
        local("rm %s" % local_dump_file)


def put_db_postgresql(local_db_name, from_file, remote_db_name):
    """
    dump local db, import on server database (must exist)
    """
    if not from_file:
        dump_name = "dump_for_%s.sql" % env.env_prefix
        local_dump_file = "./%s" % dump_name
        local(
            "pg_dump --clean --no-owner --if-exists --schema=public {database} > {file}".format(
                database=local_db_name,
                file=local_dump_file,
            )
        )
    else:
        dump_name = os.path.basename(from_file)
        local_dump_file = from_file
    remote_dump_file = os.path.join(env.project_dir, dump_name)
    put(remote_path=remote_dump_file, local_path=local_dump_file)
    if not from_file:
        local("rm %s" % local_dump_file)
    # up you go
    django_settings = _get_settings()
    remote_db_settings = django_settings.DATABASES.get("default", None)
    options, prompts = _get_postgres_options_prompts(remote_db_settings)
    with settings(prompts=prompts):
        print(prompts)
        run(
            "psql {options} {database} < {file}".format(
                options=options,
                database=remote_db_settings["NAME"],
                file=remote_dump_file,
            )
        )
    run("rm %s" % remote_dump_file)


@task
@roles("web")
def get_media():
    """
    get media files. path by convention, adapt if needed.
    """
    # trivial version
    # get(os.path.join(env.project_dir, 'public', 'media'), 'public/media')
    if getattr(env, "custom_media_root", None):
        remote_dir = env.custom_media_root
        if remote_dir[-1] == "/":
            # cannot end with a slash! rsync is not working!
            remote_dir = remote_dir[0:-1]
    else:
        remote_dir = os.path.join(
            env.project_dir,
            "public",
            "media",
        )
    local_dir = os.path.join("public")
    extra_opts = ""
    # extra_opts = "--dry-run"
    rsync_project(
        remote_dir=remote_dir,
        local_dir=local_dir,
        upload=False,
        delete=True,
        extra_opts=extra_opts,
    )


@task
@roles("web")
def put_media():
    """
    put media files. path by convention, adapt if needed.
    """
    yes_no1 = confirm(
        "Will overwrite your remote media files! Continue?",
        default=False,
    )
    if not yes_no1:
        return
    yes_no2 = confirm("Are you sure?", default=False)
    if not yes_no2:
        return

    # go for it!
    if getattr(env, "custom_media_root", None):
        cust = env.custom_media_root
        remote_dir, to_remove = os.path.split(env.custom_media_root)
        if not to_remove:
            # custom media root ended with a slash - let's do it again!
            remote_dir, to_remove = os.path.split(cust)
    else:
        remote_dir = os.path.join(
            env.project_dir,
            "public",
        )
    local_dir = os.path.join("public", "media")
    extra_opts = ""
    # extra_opts = "--dry-run"
    rsync_project(
        remote_dir=remote_dir,
        local_dir=local_dir,
        upload=True,
        delete=True,
        extra_opts=extra_opts,
    )


# ==============================================================================
# Helper functions
# ==============================================================================


def virtualenv(command):
    """
    Run a command in the virtualenv. This prefixes the command with the source
    command.
    Usage:
        virtualenv('pip install django')
    """
    source = "source {virtualenv_dir}/bin/activate && ".format(**env)
    run(source + command)


@task
@roles("web")
def dj(command):
    """
    Run a Django manage.py command on the server.
    """
    cmd_prefix = "cd {project_dir}".format(**env)
    if getattr(env, "custom_manage_py_root", None):
        cmd_prefix = "cd {}".format(env.custom_manage_py_root)
    source_env = ""
    if getattr(env, "env_file", None):
        source_env = " && source ../envs/.env-{env_prefix}".format(**env)
    virtualenv(
        "{cmd_prefix} {source_env} && export DJANGO_SETTINGS_MODULE={project_conf} && ./manage.py {dj_command}".format(
            dj_command=command, cmd_prefix=cmd_prefix, source_env=source_env, **env
        )
    )


@task
@roles("web")
def shell(command):
    """
    Run an arbitrary command on the server.
    """
    run(command)


@task
@roles("web")
def memory():
    """
    Run an arbitrary command on the server.
    """
    run(
        "ps -U %s --no-headers -o rss | awk '{ sum+=$1} END {print int(sum/1024) \"MB\"}'"
        % (env.main_user)
    )


def fix_permissions(path="."):
    """
    Fix the file permissions. what a hack.
    """
    puts("no need for fixing permissions yet!")
    return


def _get_settings(conf=None):
    # do this here. django settings cannot be imported more than once...probably.
    # still dont really get the mess here.
    if not conf:
        conf = env.project_conf
    django.settings_module(conf)
    from django.conf import settings

    return settings


def _get_my_cnf_name():
    return ".{project_name}-{env_prefix}.cnf".format(**env)


def _get_local_db_name():
    local_db_name = getattr(env, "local_db_name", None)
    if not local_db_name:
        local_db_name = env.project_name
    return local_db_name


def _get_remote_db_name():
    remote_db_name = getattr(env, "remote_db_name", None)
    if not remote_db_name:
        settings = _get_settings()
        db_settings = settings.DATABASES
        remote_db_name = db_settings["default"]["NAME"]
    return remote_db_name
