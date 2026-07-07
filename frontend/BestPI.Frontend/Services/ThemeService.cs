using Microsoft.JSInterop;

namespace BestPI.Frontend.Services;

public enum ThemePreference
{
    System,
    Light,
    Dark,
}

public interface IThemeClient
{
    Task<ThemePreference?> GetSavedPreferenceAsync(CancellationToken cancellationToken = default);
    Task SetPreferenceAsync(ThemePreference preference, CancellationToken cancellationToken = default);
    Task ClearPreferenceAsync(CancellationToken cancellationToken = default);
    Task ApplyAsync(ThemePreference preference, CancellationToken cancellationToken = default);
}

public sealed class ThemeService
{
    private readonly IThemeClient _client;
    private bool _initialized;

    public ThemeService(IThemeClient client)
    {
        _client = client;
    }

    public ThemePreference Current { get; private set; } = ThemePreference.System;

    public async Task InitializeAsync(CancellationToken cancellationToken = default)
    {
        if (_initialized)
        {
            return;
        }

        var saved = await _client.GetSavedPreferenceAsync(cancellationToken);
        Current = saved ?? ThemePreference.System;
        await _client.ApplyAsync(Current, cancellationToken);
        _initialized = true;
    }

    public async Task SetThemeAsync(ThemePreference preference, CancellationToken cancellationToken = default)
    {
        Current = preference;

        if (preference == ThemePreference.System)
        {
            await _client.ClearPreferenceAsync(cancellationToken);
        }
        else
        {
            await _client.SetPreferenceAsync(preference, cancellationToken);
        }

        await _client.ApplyAsync(preference, cancellationToken);
    }
}

public sealed class BrowserThemeClient : IThemeClient
{
    private readonly IJSRuntime _jsRuntime;

    public BrowserThemeClient(IJSRuntime jsRuntime)
    {
        _jsRuntime = jsRuntime;
    }

    public async Task<ThemePreference?> GetSavedPreferenceAsync(CancellationToken cancellationToken = default)
    {
        var raw = await _jsRuntime.InvokeAsync<string?>("bestpiTheme.getPreference", cancellationToken);
        return raw switch
        {
            "light" => ThemePreference.Light,
            "dark" => ThemePreference.Dark,
            "system" => ThemePreference.System,
            null => null,
            _ => null,
        };
    }

    public Task SetPreferenceAsync(ThemePreference preference, CancellationToken cancellationToken = default)
    {
        return _jsRuntime.InvokeVoidAsync("bestpiTheme.setPreference", cancellationToken, ToRaw(preference)).AsTask();
    }

    public Task ClearPreferenceAsync(CancellationToken cancellationToken = default)
    {
        return _jsRuntime.InvokeVoidAsync("bestpiTheme.clearPreference", cancellationToken).AsTask();
    }

    public Task ApplyAsync(ThemePreference preference, CancellationToken cancellationToken = default)
    {
        return _jsRuntime.InvokeVoidAsync("bestpiTheme.applyTheme", cancellationToken, ToRaw(preference)).AsTask();
    }

    private static string ToRaw(ThemePreference preference) => preference switch
    {
        ThemePreference.Light => "light",
        ThemePreference.Dark => "dark",
        _ => "system",
    };
}
