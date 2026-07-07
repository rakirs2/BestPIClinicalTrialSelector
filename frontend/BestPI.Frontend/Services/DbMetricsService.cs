using System.Globalization;
using Microsoft.Extensions.Logging;
using Npgsql;

namespace BestPI.Frontend.Services;

public record DbSizeSummary(long Bytes, string Pretty);

public record DbHealthSnapshot(
    string Status,
    long SizeBytes,
    string SizePretty,
    double UptimeSeconds,
    int Connections,
    int MaxConnections,
    double ConnectionUtilization,
    DateTime CheckedAt,
    DateTime? LastVacuum
);

public class DbMetricsService
{
    private readonly NpgsqlDataSource _dataSource;
    private readonly ILogger<DbMetricsService> _logger;

    public DbMetricsService(NpgsqlDataSource dataSource, ILogger<DbMetricsService> logger)
    {
        _dataSource = dataSource;
        _logger = logger;
    }

    public async Task<DbHealthSnapshot> GetHealthAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            await using var connection = await _dataSource.OpenConnectionAsync(cancellationToken);

            var metricsCommand = connection.CreateCommand();
            metricsCommand.CommandText = """
WITH stats AS (
    SELECT
        pg_database_size(current_database()) AS size_bytes,
        pg_size_pretty(pg_database_size(current_database())) AS size_pretty,
        EXTRACT(EPOCH FROM (now() - pg_postmaster_start_time()))::double precision AS uptime_seconds,
        psd.numbackends
    FROM pg_stat_database psd
    WHERE psd.datname = current_database()
),
vac AS (
    SELECT MAX(GREATEST(last_vacuum, last_autovacuum)) AS last_vacuum
    FROM pg_stat_all_tables
)
SELECT stats.size_bytes,
       stats.size_pretty,
        stats.uptime_seconds,
        stats.numbackends,
        vac.last_vacuum
FROM stats, vac;
""";

            await using var reader = await metricsCommand.ExecuteReaderAsync(cancellationToken);
            if (!await reader.ReadAsync(cancellationToken))
            {
                throw new InvalidOperationException("Unable to read database metrics.");
            }

            var sizeBytes = reader.IsDBNull(0) ? 0 : reader.GetInt64(0);
            var sizePretty = reader.IsDBNull(1) ? "0 MB" : reader.GetString(1);
            var uptimeSeconds = reader.IsDBNull(2) ? 0d : reader.GetDouble(2);
            var connections = reader.IsDBNull(3) ? 0 : reader.GetInt32(3);
            DateTime? lastVacuum = reader.IsDBNull(4) ? null : reader.GetDateTime(4);

            await reader.DisposeAsync();

            var maxConnections = await GetMaxConnectionsAsync(connection, cancellationToken);
            var utilization = maxConnections == 0 ? 0d : Math.Round(connections / (double)maxConnections * 100d, 2);
            var status = DetermineStatus(connections, maxConnections);

            return new DbHealthSnapshot(
                status,
                sizeBytes,
                sizePretty,
                uptimeSeconds,
                connections,
                maxConnections,
                utilization,
                DateTime.UtcNow,
                lastVacuum
            );
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to compute database health snapshot");
            return new DbHealthSnapshot(
                "unreachable",
                0,
                "0 MB",
                0,
                0,
                0,
                0,
                DateTime.UtcNow,
                null
            );
        }
    }

    public async Task<DbSizeSummary> GetDatabaseSizeAsync(CancellationToken cancellationToken = default)
    {
        var snapshot = await GetHealthAsync(cancellationToken);
        return new DbSizeSummary(snapshot.SizeBytes, snapshot.SizePretty);
    }

    private static string DetermineStatus(int connections, int maxConnections)
    {
        if (maxConnections <= 0)
        {
            return "healthy";
        }

        var utilization = connections / (double)maxConnections;
        if (utilization >= 0.95)
        {
            return "critical";
        }

        if (utilization >= 0.8)
        {
            return "warning";
        }

        return "healthy";
    }

    private static async Task<int> GetMaxConnectionsAsync(NpgsqlConnection connection, CancellationToken cancellationToken)
    {
        await using var cmd = connection.CreateCommand();
        cmd.CommandText = "SHOW max_connections";
        var result = await cmd.ExecuteScalarAsync(cancellationToken);
        if (result is null)
        {
            return 0;
        }

        if (int.TryParse(Convert.ToString(result, CultureInfo.InvariantCulture), out var maxConnections))
        {
            return maxConnections;
        }

        return 0;
    }
}
