using System.Globalization;

namespace BestPI.Frontend.Components.Pages;

public static class ScraperStatusFormatting
{
    private static readonly Dictionary<string, string> StatusLabels = new(StringComparer.OrdinalIgnoreCase)
    {
        ["running"] = "Running",
        ["completed"] = "Completed",
        ["failed"] = "Failed",
        ["stopped_manual"] = "Stopped (Manual)",
        ["stopped_threshold"] = "Stopped (Threshold)",
    };

    public static string ToDisplayLabel(string? status)
    {
        if (string.IsNullOrWhiteSpace(status))
        {
            return "Unknown";
        }

        if (StatusLabels.TryGetValue(status, out var label))
        {
            return label;
        }

        var normalized = status.Replace('_', ' ');
        return CultureInfo.InvariantCulture.TextInfo.ToTitleCase(normalized.ToLowerInvariant());
    }
}
