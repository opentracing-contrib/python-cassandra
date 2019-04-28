[![PyPI version][pypi-img]][pypi] [![Build Status][ci-img]][ci] [![Coverage Status][cov-img]][cov]


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

This will automatically trace all your queries (except for `BatchStatement`, see Known Issues). The default span operation name will be the query string, e.g: `SELECT * FROM test`

If you query contains parameters, the query will include the `%s` or `?`

### Using fixed span name

```python
QueryTracing(self.session, span_name='execute')
```

All the spans will be sent to the tracer with the name `execute`.

### Using a prefix

```python
QueryTracing(self.session, prefix='Custom')
```

All the spans will contain a prefix and it will looke like: "Custom: SELECT * FROM..."

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

## Known Issues

- BatchStatement are yet unsupported as there is no simple way to get the executed query strings.
- Queries that override the keyspace (`SELECT * FROM keyspace.table`) won't have the overriden keyspace sent to the tracer.


[ci-img]: https://travis-ci.org/nicholasamorim/opentracing-python-cassandra.svg?branch=master
[ci]: https://travis-ci.org/nicholasamorim/opentracing-python-cassandra
