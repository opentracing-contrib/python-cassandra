import opentracing
from opentracing.ext import tags
# from cassandra.query import SimpleStatement, PreparedStatement


class QueryTracing:
    def __init__(self, session, tracer=None, span_tags=None):
        self._tracer = tracer or opentracing.tracer
        self.session = session
        session.add_request_init_listener(self.on_request)
        self._span_tags = span_tags or {}

    def get_span_name(self):
        return 'execute'

    def on_request(self, rf):
        query_string = self.get_query_string(rf)
        active = opentracing.tracer.scope_manager.active
        span = opentracing.tracer.start_span(query_string, child_of=active.span)

        span.set_tag(tags.DATABASE_TYPE, 'cassandra')
        span.set_tag(tags.COMPONENT, 'cassandra-driver')
        span.set_tag(tags.DATABASE_INSTANCE, self.get_keyspace(rf) or self.session.keyspace)
        span.set_tag(tags.DATABASE_STATEMENT, query_string)
        span.set_tag('command', self.get_operation(query_string))

        for tag, value in self._span_tags.items():
            span.set_tag(tag, value)

        rf.add_callbacks(self.on_success, self.on_error, callback_args=(rf, span), errback_args=(rf, span))

    def on_success(self, _, rf, span):
        if span is None:
            return

        span.set_tag('reported_duration', 1)
        span.finish()

    def on_error(self, _, rf, span):
        if span is None:
            return

        span.set_tag(tags.ERROR, True)
        span.finish()

    def get_keyspace(self, rf):
        return rf.query.keyspace

    def get_query_string(self, rf):
        return rf.query.query_string

    def get_operation(self, query_string):
        qs = query_string[:30].upper()
        for command in CQL_COMMANDS:
            if qs.startswith(command):
                return command


CQL_COMMANDS = (
    'SELECT',
    'INSERT',
    'UPDATE'
    'DELETE',
    'CREATE KEYSPACE',
    'BATCH',
    'ALTER KEYSPACE',
    'ALTER MATERIALIZED VIEW',
    'ALTER ROLE',
    'ALTER TABLE',
    'ALTER TYPE',
    'ALTER USER',
    'CREATE AGGREGATE',
    'CREATE INDEX',
    'CREATE FUNCTION',
    'CREATE MATERIALIZED VIEW',
    'CREATE TABLE',
    'CREATE TRIGGER',
    'CREATE TYPE',
    'CREATE ROLE',
    'CREATE USER',
    'DROP AGGREGATE',
    'DROP FUNCTION',
    'DROP INDEX',
    'DROP KEYSPACE',
    'DROP MATERIALIZED VIEW',
    'DROP ROLE',
    'DROP TABLE',
    'DROP TRIGGER',
    'DROP TYPE',
    'DROP USER',
    'GRANT',
    'LIST PERMISSIONS',
    'LIST ROLES',
    'LIST USERS',
    'REVOKE',
    'TRUNCATE',
    'USE',
)
