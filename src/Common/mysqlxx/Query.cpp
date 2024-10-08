#if __has_include(<mysql.h>)
#include <errmsg.h>
#include <mysql.h>
#else
#include <mysql/errmsg.h>
#include <mysql/mysql.h>
#endif

#include <Common/logger_useful.h>

#include <mysqlxx/Connection.h>
#include <mysqlxx/Query.h>
#include <mysqlxx/Types.h>


namespace mysqlxx
{

Query::Query(Connection * conn_, const std::string & query_string) : conn(conn_)
{
    /// Makes sense if called from the other thread than Connection.
    mysql_thread_init();

    query = query_string;
}

Query::Query(const Query & other) : conn(other.conn)
{
    /// Makes sense if called from the other thread than Connection.
    mysql_thread_init();

    query = other.query;
}

Query & Query::operator= (const Query & other)
{
    if (this == &other)
        return *this;

    conn = other.conn;
    query = other.query;

    return *this;
}

Query::~Query()
{
    mysql_thread_end();
}

void Query::executeImpl()
{
    MYSQL* mysql_driver = conn->getDriver();

    LOG_TRACE(&Poco::Logger::get("mysqlxx::Query"), "Running MySQL query using connection {}", mysql_thread_id(mysql_driver));
    if (mysql_real_query(mysql_driver, query.data(), query.size()))
    {
        const auto err_no = mysql_errno(mysql_driver);
        switch (err_no)
        {
        case CR_SERVER_GONE_ERROR:
            [[fallthrough]];
        case CR_SERVER_LOST:
            throw ConnectionLost(errorMessage(mysql_driver), err_no);
        default:
            throw BadQuery(errorMessage(mysql_driver, query), err_no);
        }
    }
}

UseQueryResult Query::use()
{
    executeImpl();
    MYSQL_RES * res = mysql_use_result(conn->getDriver());
    if (!res)
        onError(conn->getDriver());

    return UseQueryResult(res, conn, this);
}

void Query::execute()
{
    executeImpl();
}

UInt64 Query::insertID()
{
    return mysql_insert_id(conn->getDriver());
}

}
