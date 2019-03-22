from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from flask import current_app
config.set_main_option('sqlalchemy.url', current_app.config.get('SQLALCHEMY_DATABASE_URI'))
target_metadata = current_app.extensions['migrate'].db.metadata

def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in [
        'Class_assistant_campuses',
        'Class_bundle',
        'Class_operation',
        'Class_recipe',
        'Class_report',
        'Class_schedule_assistants',
        'Class_schedule_teachers',
        'Class_setup',
        'Class_shoppinglist',
        'Class_teacher',
        'Class_text',
        # 'Class_waitinglist',
        'Email_message',
        'Newsletter_archive',
        'Shop_certificateorder',
        'Shop_certificateproductsaleitem',
        'Shop_creditcard',
        'Shop_guest',
        'Shop_order',
        'alembic_version',
        'assistants',
        'auth_group',
        'auth_group_permissions',
        'auth_message',
        'auth_permission',
        'auth_user',
        'auth_user_groups',
        'auth_user_notes',
        'auth_user_user_permissions',
        'captcha_captchastore',
        'certificates',
        'classes',
        'descriptions',
        'django_admin_log',
        'django_content_type',
        'django_session',
        'orders',
        'reservations',
        'setup_round',
        'setup_round_point',
        'students',
        'teachers',
        'waitinglist',]:
        return False
    else:
        return True

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url)

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    engine = engine_from_config(
                config.get_section(config.config_ini_section),
                prefix='sqlalchemy.',
                poolclass=pool.NullPool)

    connection = engine.connect()
    context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_object = include_object
                )

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
