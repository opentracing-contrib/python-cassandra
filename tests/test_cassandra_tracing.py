# -*- coding: utf-8 -*-
import unittest

from cassandra import InvalidRequest
from cassandra.cluster import Cluster
from opentracing.mocktracer import MockTracer
from cassandra_opentracing.tracing import QueryTracing


class TestCassandra(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cluster = Cluster()
        session = cluster.connect()
        session.execute("DROP KEYSPACE IF EXISTS test", timeout=10)
        session.execute(
            "CREATE KEYSPACE if not exists test WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor': 1};",
            timeout=10,
        )

        session.execute(
            "CREATE TABLE if not exists test.luthier (name text PRIMARY KEY, location text)"
        )
        session.execute(
            "CREATE TABLE if not exists test.painter (name text PRIMARY KEY, age int, description text)"
        )

        session.execute(
            "INSERT INTO test.luthier (name, location) VALUES ('Mina', 'Eesti')"
        )
        session.execute(
            "INSERT INTO test.luthier (name, location) VALUES ('Tema', 'Eesti Jälle')"
        )

        session.execute(
            "INSERT INTO test.painter (name, age, description) VALUES ('Love', 29, 'The Best')"
        )

    @classmethod
    def tearDownClass(cls):
        cluster = Cluster()
        session = cluster.connect()
        session.execute("DROP KEYSPACE IF EXISTS test", timeout=10)

    def setUp(self):
        self.cluster = Cluster()
        self.session = self.cluster.connect("test")
        self.tracer = MockTracer()
        self.qt = QueryTracing(self.session, tracer=self.tracer)

    def assertTags(
        self, tags, keyspace, statement, command, paginated=False, additional_tags=None
    ):
        self.assertEqual(tags["db.type"], "cassandra")
        self.assertEqual(tags["component"], "cassandra-driver")
        self.assertEqual(tags["db.instance"], keyspace)
        self.assertEqual(tags["db.statement"], statement)
        self.assertEqual(tags["command"], command)
        self.assertEqual(tags["paginated"], False)
        self.assertTrue(isinstance(tags["reported_duration"], float))

        if additional_tags:
            for key, value in additional_tags.items():
                self.assertEqual(tags[key], value)

    def test_simple_statement_select(self):
        statement = "SELECT * FROM luthier"
        self.session.execute(statement)
        spans = self.tracer.finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.operation_name, 'execute')
        self.assertTags(span.tags, "test", statement, "SELECT")

    def test_simple_statement_select_query_as_name(self):
        self.session = self.cluster.connect("test")
        self.qt = QueryTracing(
            self.session, tracer=self.tracer, span_tags={"one": "more", "tag": 2},
            use_querystring_as_name=True
        )
        statement = "SELECT * FROM luthier"
        self.session.execute(statement)
        spans = self.tracer.finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.operation_name, statement)
        self.assertTags(span.tags, "test", statement, "SELECT")

    def test_simple_statement_select_with_parent_span(self):
        statement = "SELECT * FROM luthier"
        with self.tracer.start_active_span("simple"):
            self.session.execute(statement)
        spans = self.tracer.finished_spans()
        self.assertEqual(len(spans), 2)
        self.assertEqual(spans[1].operation_name, "simple")
        query_span = spans[0]
        self.assertEqual(query_span.operation_name, 'execute')
        self.assertTags(query_span.tags, "test", statement, "SELECT")

    def test_prepared_statement_select(self):
        statement = "SELECT * FROM luthier WHERE name = ?"
        prepared = self.session.prepare(statement)
        self.session.execute(prepared, ("Mina",))
        spans = self.tracer.finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertTags(span.tags, "test", statement, "SELECT")

    def test_select_error(self):
        statement = "SELECT * FROM luthier WHERE no = true"
        try:
            self.session.execute(statement)
        except Exception:
            pass

        spans = self.tracer.finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertTags(span.tags, "test", statement, "SELECT")
        print(
            span.logs[0].key_values,
            {
                "event": "error",
                "error.object": InvalidRequest(
                    'Error from server: code=2200 [Invalid query] message="Undefined column name no"'
                ),
            },
        )

    def test_simple_statement_select_custom_tags(self):
        self.session = self.cluster.connect("test")
        self.qt = QueryTracing(
            self.session, tracer=self.tracer, span_tags={"one": "more", "tag": 2}
        )
        statement = "SELECT * FROM luthier"
        self.session.execute(statement)
        spans = self.tracer.finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.operation_name, 'execute')
        self.assertTags(
            span.tags,
            "test",
            statement,
            "SELECT",
            additional_tags={"one": "more", "tag": 2},
        )

    def test_simple_statement_select_fixed_span_name(self):
        self.session = self.cluster.connect("test")
        self.qt = QueryTracing(self.session, tracer=self.tracer, span_name="One Test")
        statement = "SELECT * FROM luthier"
        self.session.execute(statement)
        spans = self.tracer.finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.operation_name, "One Test")
        self.assertTags(span.tags, "test", statement, "SELECT")

    def test_simple_statement_select_custom_prefix(self):
        self.session = self.cluster.connect("test")
        self.qt = QueryTracing(self.session, tracer=self.tracer, prefix="Custom")
        statement = "SELECT * FROM luthier"
        self.session.execute(statement)
        spans = self.tracer.finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.operation_name, "Custom: {}".format('execute'))
        self.assertTags(span.tags, "test", statement, "SELECT")
