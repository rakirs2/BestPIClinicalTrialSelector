using Npgsql;

namespace BestPI.Frontend.Services;

public record DbSizeSummary(long Bytes, string Pretty);

public class DbMetricsService
{
    private readonly NpgsqlDataSource _dataSource;

    public DbMetricsService(NpgsqlDataSource dataSource)
    {
        _dataSource = dataSource;
    }

    public async Task<DbSizeSummary> GetDatabaseSizeAsync(CancellationToken cancellationToken = default)
    {
        await using var connection = await _dataSource.OpenConnectionAsync(cancellationToken);
        await using var command = connection.CreateCommand();
        command.CommandText = "SELECT pg_database_size(current_database()), pg_size_pretty(pg_database_size(current_database()))";

        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        await reader.ReadAsync(cancellationToken);

        var bytes = reader.GetInt64(0);
        var pretty = reader.GetString(1);
        return new DbSizeSummary(bytes, pretty);
    }
}
