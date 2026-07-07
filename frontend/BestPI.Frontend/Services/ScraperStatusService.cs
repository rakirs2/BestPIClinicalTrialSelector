using Npgsql;

namespace BestPI.Frontend.Services;

public record ScraperRunSnapshot(
    Guid Id,
    string Status,
    long? TotalExpected,
    long ProcessedCount,
    int CurrentChunk,
    string? LastPageToken,
    string? Notes,
    string? LastError,
    DateTime StartedAt,
    DateTime? FinishedAt
);

public record ScraperStatusSnapshot(
    ScraperRunSnapshot? LatestRun,
    IReadOnlyList<ScraperRunSnapshot> RecentRuns,
    DateTime RetrievedAt
);

public class ScraperStatusService
{
    private readonly NpgsqlDataSource _dataSource;

    public ScraperStatusService(NpgsqlDataSource dataSource)
    {
        _dataSource = dataSource;
    }

    public async Task<ScraperStatusSnapshot> GetStatusAsync(int limit = 20, CancellationToken cancellationToken = default)
    {
        limit = Math.Clamp(limit, 1, 100);

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
            var snapshot = new ScraperRunSnapshot(
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
            );

            runs.Add(snapshot);
        }

        return new ScraperStatusSnapshot(
            runs.FirstOrDefault(),
            runs,
            DateTime.UtcNow
        );
    }
}
