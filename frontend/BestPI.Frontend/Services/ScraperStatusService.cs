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

public record ScraperRunLogEntry(
    DateTime LoggedAt,
    string Level,
    string Message
);

public record ScraperStatusSnapshot(
    ScraperRunSnapshot? LatestRun,
    IReadOnlyList<ScraperRunSnapshot> RecentRuns,
    IReadOnlyList<ScraperRunLogEntry> LatestRunLogs,
    DateTime RetrievedAt
);

public class ScraperStatusService
{
    private readonly IScraperStatusStore _store;

    public ScraperStatusService(IScraperStatusStore store)
    {
        _store = store;
    }

    public async Task<ScraperStatusSnapshot> GetStatusAsync(int limit = 20, CancellationToken cancellationToken = default)
    {
        limit = Math.Clamp(limit, 1, 100);

        var runs = await _store.GetRecentRunsAsync(limit, cancellationToken);
        var latestRun = runs.FirstOrDefault();
        var logs = latestRun is not null
            ? await _store.GetLogsForRunAsync(latestRun.Id, cancellationToken)
            : Array.Empty<ScraperRunLogEntry>();

        return new ScraperStatusSnapshot(
            latestRun,
            runs,
            logs,
            DateTime.UtcNow
        );
    }
}
