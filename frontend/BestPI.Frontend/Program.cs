using BestPI.Frontend.Components;
using BestPI.Frontend.Services;
using Npgsql;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();
builder.Services.AddHttpClient();

var connectionString = builder.Configuration.GetConnectionString("Postgres");
if (string.IsNullOrWhiteSpace(connectionString))
{
    throw new InvalidOperationException("ConnectionStrings:Postgres is not configured.");
}
builder.Services.AddNpgsqlDataSource(connectionString);
builder.Services.AddScoped<DbMetricsService>();
builder.Services.AddScoped<IScraperStatusStore, PostgresScraperStatusStore>();
builder.Services.AddScoped<ScraperStatusService>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
}
app.UseStatusCodePagesWithReExecute("/not-found", createScopeForStatusCodePages: true);
app.UseAntiforgery();

app.MapStaticAssets();
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.MapGet("/api/db-health", async (DbMetricsService metricsService, CancellationToken cancellationToken) =>
{
    var snapshot = await metricsService.GetHealthAsync(cancellationToken);
    return Results.Ok(snapshot);
});

app.MapGet("/api/db-size", async (DbMetricsService metricsService, CancellationToken cancellationToken) =>
{
    var summary = await metricsService.GetDatabaseSizeAsync(cancellationToken);
    return Results.Ok(summary);
});

app.MapGet("/api/scraper-status", async (ScraperStatusService scraperStatusService, CancellationToken cancellationToken, int limit = 20) =>
{
    var snapshot = await scraperStatusService.GetStatusAsync(limit == 0 ? 20 : limit, cancellationToken);
    return Results.Ok(snapshot);
});

app.Run();
