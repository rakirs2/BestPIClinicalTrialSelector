using BestPI.Frontend.Components.Pages;

namespace BestPI.Frontend.Tests.Components;

[TestClass]
public class ScraperStatusFormattingTests
{
    [DataTestMethod]
    [DataRow("running", "Running")]
    [DataRow("completed", "Completed")]
    [DataRow("stopped_manual", "Stopped (Manual)")]
    [DataRow("stopped_threshold", "Stopped (Threshold)")]
    [DataRow("FAILED", "Failed")]
    public void KnownStatuses_MapToLabels(string input, string expected)
    {
        var label = ScraperStatusFormatting.ToDisplayLabel(input);
        Assert.AreEqual(expected, label);
    }

    [TestMethod]
    public void UnknownStatus_TitlesWords()
    {
        var label = ScraperStatusFormatting.ToDisplayLabel("partial_refresh");
        Assert.AreEqual("Partial Refresh", label);
    }

    [TestMethod]
    public void NullStatus_ReturnsUnknown()
    {
        var label = ScraperStatusFormatting.ToDisplayLabel(null);
        Assert.AreEqual("Unknown", label);
    }
}
