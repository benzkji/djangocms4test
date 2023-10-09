from fabric.api import task, env

from fabric_bnzk.tasks import *  # noqa


env.is_python3 = True
env.project_name = "djangocms4test"
env.repository = "git@gitXY.org:bnzk/{project_name}.git".format(**env)
env.sites = ("djangocms4test",)
env.is_postgresql = True  # False for mysql! only used for put/get_db
env.needs_main_nginx_files = True
env.is_supervisord = True
env.is_nginx_gunicorn = True
env.is_uwsgi = False
env.is_apache = False
env.is_webpack = True
env.remote_ref = "origin/main"
# these will be checked for changes
env.requirements_files = [
    "requirements/deploy.txt",
    "requirements/deploy.in",
    "requirements/basic.in",
]
# this is used with pip install -r
env.requirements_file = env.requirements_files[0]


# ==============================================================================
# Tasks which set up deployment environments
# ==============================================================================


@task
def live():
    """
    Use the live deployment environment.
    """
    env.env_prefix = "live"
    env.deploy_crontab = True
    env.main_user = "{project_name}".format(**env)
    server = "{main_user}@s20.wservices.ch".format(**env)
    env.roledefs = {
        "web": [server],
        "db": [server],
    }
    generic_env_settings()


@task
def stage():
    """
    Use the sandbox deployment environment on xy.bnzk.ch.
    """
    env.env_prefix = "stage"
    env.deploy_crontab = False
    env.main_user = "{project_name}".format(**env)
    server = "{main_user}@s20.wservices.ch".format(**env)
    env.roledefs = {
        "web": [server],
        "db": [server],
    }
    generic_env_settings()


def generic_env_settings():
    if not getattr(env, "deploy_crontab", None):
        env.deploy_crontab = False
    env.project_dir = "/home/{main_user}/sites/{project_name}-{env_prefix}".format(
        **env
    )
    env.virtualenv_dir = "{project_dir}/virtualenv".format(**env)
    env.gunicorn_restart_command = "~/init/{site}-{env_prefix}.sh restart"
    env.gunicorn_stop_command = "~/init/{site}-{env_prefix}.sh stop"
    env.nginx_restart_command = "~/init/nginx.sh restart"
    # not needed with uwsgi emporer mode, cp is enough
    # env.uwsgi_restart_command = 'touch $HOME/uwsgi.d/{site}-{env_prefix}.ini'
    # env.project_conf = 'project.settings._{project_name}_{env_prefix}'.format(**env)
    env.project_conf = "project.settings".format(**env)
    env.env_file = "project/.env-{env_prefix}".format(**env)


stage()
