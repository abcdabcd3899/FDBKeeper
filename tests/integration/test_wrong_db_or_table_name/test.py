import pytest
from helpers.client import QueryRuntimeException
from helpers.cluster import ClickHouseCluster
from helpers.test_tools import TSV

cluster = ClickHouseCluster(__file__)
node = cluster.add_instance("node")


@pytest.fixture(scope="module")
def start():
    try:
        cluster.start()
        yield cluster
    finally:
        cluster.shutdown()


def test_wrong_database_name(start):
    node.query(
        """
        CREATE DATABASE test;
        CREATE TABLE test.table_test (i Int64) ENGINE=Memory;
        INSERT INTO test.table_test SELECT 1;
        """
    )

    with pytest.raises(
        QueryRuntimeException,
        match="DB::Exception: Database tes does not exist. Maybe you meant test?.",
    ):
        node.query("SELECT * FROM tes.table_test LIMIT 1;")
    assert int(node.query("SELECT count() FROM test.table_test;")) == 1
    node.query(
        """
        DROP TABLE test.table_test;
        DROP DATABASE test;
        """
    )


def test_drop_wrong_database_name(start):
    node.query(
        """
        CREATE DATABASE test;
        CREATE TABLE test.table_test (i Int64) ENGINE=Memory;
        INSERT INTO test.table_test SELECT 1;
        """
    )

    with pytest.raises(
        QueryRuntimeException,
        match="DB::Exception: Database tes does not exist. Maybe you meant test?.",
    ):
        node.query("DROP DATABASE tes;")
    assert int(node.query("SELECT count() FROM test.table_test;")) == 1
    node.query("DROP DATABASE test;")


def test_wrong_table_name(start):
    node.query(
        """
        CREATE DATABASE test;
        CREATE DATABASE test2;
        CREATE TABLE test.table_test (i Int64) ENGINE=Memory;
        CREATE TABLE test.table_test2 (i Int64) ENGINE=Memory;
        INSERT INTO test.table_test SELECT 1;
        """
    )
    with pytest.raises(
        QueryRuntimeException,
        match="DB::Exception: Table test.table_test1 does not exist. Maybe you meant test.table_test?.",
    ):
        node.query(
            """
            SELECT * FROM test.table_test1 LIMIT 1;
            """
        )
    assert int(node.query("SELECT count() FROM test.table_test;")) == 1

    with pytest.raises(
        QueryRuntimeException,
        match="DB::Exception: Table test2.table_test1 does not exist. Maybe you meant test.table_test?.",
    ):
        node.query(
            """
            SELECT * FROM test2.table_test1 LIMIT 1;
            """
        )

    node.query(
        """
            DROP TABLE test.table_test;
            DROP TABLE test.table_test2;
            DROP DATABASE test;
            DROP DATABASE test2;
            """
    )


def test_drop_wrong_table_name(start):
    node.query(
        """
        CREATE DATABASE test;
        CREATE DATABASE test2;
        CREATE TABLE test.table_test (i Int64) ENGINE=Memory;
        INSERT INTO test.table_test SELECT 1;
        """
    )

    with pytest.raises(
        QueryRuntimeException,
        match="DB::Exception: Table test.table_test1 does not exist. Maybe you meant test.table_test?.",
    ):
        node.query("DROP TABLE test.table_test1;")
    assert int(node.query("SELECT count() FROM test.table_test;")) == 1

    with pytest.raises(
        QueryRuntimeException,
        match="DB::Exception: Table test2.table_test does not exist. Maybe you meant test.table_test?.",
    ):
        node.query("DROP TABLE test2.table_test;")

    node.query(
        """
        DROP TABLE test.table_test;
        DROP DATABASE test;
        DROP DATABASE test2;
        """
    )
