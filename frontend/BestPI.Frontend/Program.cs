using BestPI.Frontend.Components;
using BestPI.Frontend.Services;
using Npgsql;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

var connectionString = builder.Configuration.GetConnectionString("Postgres");
if (string.IsNullOrWhiteSpace(connectionString))
{
    throw new InvalidOperationException("ConnectionStrings:Postgres is not configured.");
}

builder.Services.AddNpgsqlDataSource(connectionString);
builder.Services.AddScoped<DbMetricsService>();

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

app.MapGet("/api/db-size", async (DbMetricsService metricsService, CancellationToken cancellationToken) =>
{
    var summary = await metricsService.GetDatabaseSizeAsync(cancellationToken);
    return Results.Ok(summary);
});

app.Run();
