import time
import opentracing
from opentracing.ext import tags
from cassandra.query import (
    SimpleStatement,
    PreparedStatement,
    BoundStatement,
    BatchStatement,
)


class QueryTracing:
    """Traces Cassandra queries.
    """

    def __init__(
        self, session, tracer=None, span_tags=None, prefix=None, span_name="execute", use_querystring_as_name=False
    ):
        """By default the span name is "execute" for all queries.
        You may adjust that either by using a custom prefix or by using an entirely
        different name by passing `span_name`.

        :param session: A `cassandra.cluster.session` to be traced.
        :param tracer: A tracer - optional. If not passed, it will just retrieve global tracer.
        :param span_tags: A dictionary of custom spam tags you may want to add.
        :param prefix: If passed, it will prefix every span name.
        :param span_name: If passed, it will be a fixed span name.
        :param use_querystring_as_name: If True, it will use the query string as the span name.
            `span_name`will be ignored, `prefix` will not be ignored.
        """
        self._tracer = tracer or opentracing.tracer
        self.session = session
        session.add_request_init_listener(self.on_request)
        self._span_tags = span_tags or {}
        self._prefix = prefix
        self._span_name = span_name
        self._use_qs_as_name = use_querystring_as_name

    def get_span_name(self, query_string):
        if self._use_qs_as_name:
            span_name = query_string
        else:
            span_name = self._span_name

        if self._prefix:
            span_name = "{}: {}".format(self._prefix, span_name)

        return span_name

    def on_request(self, rf):
        query_string = self.get_query_string(rf)
        if not query_string:
            return rf
        active = self._tracer.scope_manager.active
        span = self._tracer.start_span(
            self.get_span_name(query_string), child_of=getattr(active, "span", None)
        )

        span.set_tag(tags.DATABASE_TYPE, "cassandra")
        span.set_tag(tags.COMPONENT, "cassandra-driver")
        span.set_tag(
            tags.DATABASE_INSTANCE, self.get_keyspace(rf) or self.session.keyspace
        )
        span.set_tag(tags.DATABASE_STATEMENT, query_string)
        span.set_tag("command", self.get_operation(query_string))
        span.set_tag("paginated", getattr(rf, "has_more_pages", False))

        if rf.query.consistency_level:
            span.set_tag("consistency_level", rf.query.consistency_level)

        for tag, value in self._span_tags.items():
            span.set_tag(tag, value)

        span._cassandra_start_ts = time.time()
        rf.add_callbacks(
            self.on_success,
            self.on_error,
            callback_args=(rf, span),
            errback_args=(rf, span),
        )

    def on_success(self, _, rf, span):
        if span is None:
            return

        span.set_tag("reported_duration", time.time() - span._cassandra_start_ts)
        span.finish()

    def on_error(self, exc, rf, span):
        if span is None:
            return

        span.set_tag(tags.ERROR, True)
        span.log_kv({"event": tags.ERROR, "error.object": exc})
        span.set_tag("reported_duration", time.time() - span._cassandra_start_ts)
        span.finish()

    def get_keyspace(self, rf):
        return rf.query.keyspace

    def get_query_string(self, rf):
        query = rf.query
        if isinstance(query, (SimpleStatement, PreparedStatement)):
            return rf.query.query_string
        elif isinstance(query, BoundStatement):
            return query.prepared_statement.query_string
        elif isinstance(query, BatchStatement):
            # not implemented, can't get statement
            return
        elif isinstance(query, str):
            return query

    def get_operation(self, query_string):
        qs = query_string[:30].upper()
        for command in CQL_COMMANDS:
            if qs.startswith(command):
                return command


CQL_COMMANDS = (
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "CREATE KEYSPACE",
    "BATCH",
    "ALTER KEYSPACE",
    "ALTER MATERIALIZED VIEW",
    "ALTER ROLE",
    "ALTER TABLE",
    "ALTER TYPE",
    "ALTER USER",
    "CREATE AGGREGATE",
    "CREATE INDEX",
    "CREATE FUNCTION",
    "CREATE MATERIALIZED VIEW",
    "CREATE TABLE",
    "CREATE TRIGGER",
    "CREATE TYPE",
    "CREATE ROLE",
    "CREATE USER",
    "DROP AGGREGATE",
    "DROP FUNCTION",
    "DROP INDEX",
    "DROP KEYSPACE",
    "DROP MATERIALIZED VIEW",
    "DROP ROLE",
    "DROP TABLE",
    "DROP TRIGGER",
    "DROP TYPE",
    "DROP USER",
    "GRANT",
    "LIST PERMISSIONS",
    "LIST ROLES",
    "LIST USERS",
    "REVOKE",
    "TRUNCATE",
    "USE",
)
