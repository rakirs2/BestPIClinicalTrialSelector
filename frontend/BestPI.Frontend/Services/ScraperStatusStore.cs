using Npgsql;

namespace BestPI.Frontend.Services;

public interface IScraperStatusStore
{
    Task<IReadOnlyList<ScraperRunSnapshot>> GetRecentRunsAsync(int limit, CancellationToken cancellationToken);
    Task<IReadOnlyList<ScraperRunLogEntry>> GetLogsForRunAsync(Guid runId, CancellationToken cancellationToken);
}

public sealed class PostgresScraperStatusStore : IScraperStatusStore
{
    private readonly NpgsqlDataSource _dataSource;

    public PostgresScraperStatusStore(NpgsqlDataSource dataSource)
    {
        _dataSource = dataSource;
    }

    public async Task<IReadOnlyList<ScraperRunSnapshot>> GetRecentRunsAsync(int limit, CancellationToken cancellationToken)
    {
        var runs = new List<ScraperRunSnapshot>();

        await using var connection = await _dataSource.OpenConnectionAsync(cancellationToken);
        await using var command = connection.CreateCommand();
        command.CommandText = """
SELECT id,
       status,
       total_expected,
       processed_count,
       current_chunk,
       last_page_token,
       notes,
       last_error,
       started_at,
       finished_at
FROM ingest_runs
ORDER BY started_at DESC
LIMIT @limit;
""";
        command.Parameters.AddWithValue("limit", limit);

        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            runs.Add(new ScraperRunSnapshot(
                reader.GetGuid(0),
                reader.GetString(1),
                reader.IsDBNull(2) ? null : reader.GetInt64(2),
                reader.IsDBNull(3) ? 0 : reader.GetInt64(3),
                reader.IsDBNull(4) ? 0 : reader.GetInt32(4),
                reader.IsDBNull(5) ? null : reader.GetString(5),
                reader.IsDBNull(6) ? null : reader.GetString(6),
                reader.IsDBNull(7) ? null : reader.GetString(7),
                reader.GetDateTime(8),
                reader.IsDBNull(9) ? null : reader.GetDateTime(9)
            ));
        }

        return runs;
    }

    public async Task<IReadOnlyList<ScraperRunLogEntry>> GetLogsForRunAsync(Guid runId, CancellationToken cancellationToken)
    {
        var logs = new List<ScraperRunLogEntry>();

        await using var connection = await _dataSource.OpenConnectionAsync(cancellationToken);
        await using var command = connection.CreateCommand();
        command.CommandText = """
SELECT logged_at,
       level,
       message
FROM scraper_run_logs
WHERE run_id = @runId
ORDER BY logged_at DESC
LIMIT 50;
""";
        command.Parameters.AddWithValue("runId", runId);

        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
        while (await reader.ReadAsync(cancellationToken))
        {
            logs.Add(new ScraperRunLogEntry(
                reader.GetDateTime(0),
                reader.GetString(1),
                reader.GetString(2)
            ));
        }

        return logs;
    }
}
