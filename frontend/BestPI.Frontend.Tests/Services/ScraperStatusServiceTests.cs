using BestPI.Frontend.Services;

namespace BestPI.Frontend.Tests.Services;

[TestClass]
public class ScraperStatusServiceTests
{
    [TestMethod]
    public async Task GetStatusAsync_NoRuns_ReturnsEmptySnapshot()
    {
        var store = new FakeScraperStatusStore();
        var service = new ScraperStatusService(store);

        var snapshot = await service.GetStatusAsync();

        Assert.IsNull(snapshot.LatestRun);
        Assert.AreEqual(0, snapshot.RecentRuns.Count);
        Assert.AreEqual(0, snapshot.LatestRunLogs.Count);
        Assert.AreEqual(20, store.LastRequestedLimit);
    }

    [TestMethod]
    public async Task GetStatusAsync_ClampsRequestedLimit()
    {
        var store = new FakeScraperStatusStore();
        store.SetRuns(CreateRuns(150));
        var service = new ScraperStatusService(store);

        var snapshot = await service.GetStatusAsync(500);

        Assert.AreEqual(100, store.LastRequestedLimit);
        Assert.AreEqual(100, snapshot.RecentRuns.Count);
    }

    [TestMethod]
    public async Task GetStatusAsync_LoadsLogsForLatestRun()
    {
        var store = new FakeScraperStatusStore();
        var latestRun = new ScraperRunSnapshot(
            Guid.NewGuid(),
            "running",
            100,
            20,
            3,
            null,
            "note",
            null,
            DateTime.UtcNow.AddMinutes(-5),
            null
        );
        store.SetRuns(new[] { latestRun });
        store.SetLogs(latestRun.Id, new[]
        {
            new ScraperRunLogEntry(DateTime.UtcNow, "INFO", "Log entry")
        });

        var service = new ScraperStatusService(store);

        var snapshot = await service.GetStatusAsync();

        Assert.IsNotNull(snapshot.LatestRun);
        Assert.AreEqual(latestRun.Id, snapshot.LatestRun!.Id);
        Assert.AreEqual(1, snapshot.LatestRunLogs.Count);
        Assert.AreEqual("Log entry", snapshot.LatestRunLogs[0].Message);
    }

    private static IReadOnlyList<ScraperRunSnapshot> CreateRuns(int count)
    {
        var runs = new List<ScraperRunSnapshot>();
        for (var i = 0; i < count; i++)
        {
            runs.Add(new ScraperRunSnapshot(
                Guid.NewGuid(),
                "completed",
                null,
                i,
                i,
                null,
                null,
                null,
                DateTime.UtcNow.AddMinutes(-i),
                DateTime.UtcNow.AddMinutes(-i + 1)
            ));
        }

        return runs;
    }

    private sealed class FakeScraperStatusStore : IScraperStatusStore
    {
        private IReadOnlyList<ScraperRunSnapshot> _runs = Array.Empty<ScraperRunSnapshot>();
        private readonly Dictionary<Guid, IReadOnlyList<ScraperRunLogEntry>> _logs = new();

        public int LastRequestedLimit { get; private set; } = 1;

        public void SetRuns(IReadOnlyList<ScraperRunSnapshot> runs)
        {
            _runs = runs;
        }

        public void SetLogs(Guid runId, IReadOnlyList<ScraperRunLogEntry> entries)
        {
            _logs[runId] = entries;
        }

        public Task<IReadOnlyList<ScraperRunSnapshot>> GetRecentRunsAsync(int limit, CancellationToken cancellationToken)
        {
            LastRequestedLimit = limit;
            return Task.FromResult<IReadOnlyList<ScraperRunSnapshot>>(_runs.Take(limit).ToList());
        }

        public Task<IReadOnlyList<ScraperRunLogEntry>> GetLogsForRunAsync(Guid runId, CancellationToken cancellationToken)
        {
            if (_logs.TryGetValue(runId, out var entries))
            {
                return Task.FromResult(entries);
            }

            return Task.FromResult<IReadOnlyList<ScraperRunLogEntry>>(Array.Empty<ScraperRunLogEntry>());
        }
    }
}
