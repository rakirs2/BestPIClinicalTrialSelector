using System.Linq;
using BestPI.Frontend.Services;

namespace BestPI.Frontend.Tests.Services;

[TestClass]
public class ThemeServiceTests
{
    [TestMethod]
    public async Task InitializeAsync_AppliesSavedPreference()
    {
        var client = new FakeThemeClient { SavedPreference = ThemePreference.Dark };
        var service = new ThemeService(client);

        await service.InitializeAsync();

        Assert.AreEqual(ThemePreference.Dark, service.Current);
        Assert.AreEqual(1, client.ApplyCalls.Count);
        Assert.AreEqual(ThemePreference.Dark, client.ApplyCalls[0]);
    }

    [TestMethod]
    public async Task SetThemeAsync_PersistsNonSystemPreference()
    {
        var client = new FakeThemeClient();
        var service = new ThemeService(client);

        await service.SetThemeAsync(ThemePreference.Light);

        CollectionAssert.Contains(client.SetCalls, ThemePreference.Light);
        Assert.AreEqual(0, client.ClearCalls);
    }

    [TestMethod]
    public async Task SetThemeAsync_ClearsSystemPreference()
    {
        var client = new FakeThemeClient();
        var service = new ThemeService(client);

        await service.SetThemeAsync(ThemePreference.System);

        Assert.AreEqual(1, client.ClearCalls);
        Assert.AreEqual(ThemePreference.System, client.ApplyCalls.Last());
    }

    private sealed class FakeThemeClient : IThemeClient
    {
        public ThemePreference? SavedPreference { get; set; }
        public List<ThemePreference> ApplyCalls { get; } = new();
        public List<ThemePreference> SetCalls { get; } = new();
        public int ClearCalls { get; private set; }

        public Task<ThemePreference?> GetSavedPreferenceAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult(SavedPreference);
        }

        public Task SetPreferenceAsync(ThemePreference preference, CancellationToken cancellationToken = default)
        {
            SetCalls.Add(preference);
            return Task.CompletedTask;
        }

        public Task ClearPreferenceAsync(CancellationToken cancellationToken = default)
        {
            ClearCalls++;
            return Task.CompletedTask;
        }

        public Task ApplyAsync(ThemePreference preference, CancellationToken cancellationToken = default)
        {
            ApplyCalls.Add(preference);
            return Task.CompletedTask;
        }
    }
}
