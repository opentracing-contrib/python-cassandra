[![Build Status][ci-img]][ci] [![Coverage Status][cov-img]][cov]


# opentracing-python-cassandra

Instrumentation tools to enable tracing for [cassandra-driver](https://github.com/datastax/python-driver).

```
pip install cassandra_opentracing
```

## Usage


```python
# set up your tracer
cluster = Cluster()
session = cluster.connect('my_keyspace')
QueryTracing(self.session)
```

This will automatically trace all your queries (except for `BatchStatement`, see Known Issues). The default span operation name is `execute` for all queries. Operation name are meant to be low cardinality and there's a standard tag for the query statement: `db.statement`.


### Using fixed span name

```python
QueryTracing(self.session, span_name='execute')
```

All the spans will be sent to the tracer with the name `execute`. Note the query string will still be sent in the tag `db.statement`.

### Using a prefix

```python
QueryTracing(self.session, prefix='Custom')
```

All the spans will contain a prefix and it will looke like: "Custom: SELECT * FROM..."

### Using query string as span name

```python
# set up your tracer
cluster = Cluster()
session = cluster.connect('my_keyspace')
QueryTracing(self.session, use_querystring_as_name=True)
```

If you query contains parameters, the query will include the `%s` or `?`. The span will be the query string, e.g: `SELECT * FROM test_table WHERE name = %s`.

When passing `use_querystring_as_name`, you can still use `prefix` but any value passed in `span_name` will be ignored.

### Adding more span tags

All you have to is:

```python
cluster = Cluster()
session = cluster.connect('my_keyspace')
QueryTracing(self.session, span_tags={'custom_tag': 'value'})
```

All queries will contain the custom tags.

### Using a custom tracer

You may pass a `tracer` argument to QueryTracing. If you don't, the default `opentracing.tracer` will be used.

## Tags

All traces will contain the following tags:

### OpenTracing standard tags:

- `db.type`: cassandra
- `component`: `cassandra-driver`
- `db.instance`: The execution keyspace except when the keyspace is overriden on the query string (see Known Issues).
- `db.statement`: The query string itself.
- `consistency_level`: If the query specified a consistency level, this tag will be present.
- `error`: In case of error, this will be set to True and a log will be issued with the error message.

### Tags added by this library

- `command`: This indicates the CQL operation, e.g: `SELECT`, `UPDATE`, `CREATE KEYSPACE`, etc.
- `paginated`: If the query is pagined, this will be set to True.
- `reported_duration`: The time taken to execute the query. Note that this time takes into account the network roundtrip as well.

## Known Issues

- BatchStatement are yet unsupported as there is no simple way to get the executed query strings.
- Queries that override the keyspace (`SELECT * FROM keyspace.table`) won't have the overriden keyspace sent to the tracer.


[ci-img]: https://travis-ci.org/nicholasamorim/opentracing-python-cassandra.svg?branch=master
[ci]: https://travis-ci.org/nicholasamorim/opentracing-python-cassandra
[cov-img]: https://codecov.io/gh/nicholasamorim/opentracing-python-cassandra/branch/master/graph/badge.svg
[cov]: https://codecov.io/gh/nicholasamorim/opentracing-python-cassandra
