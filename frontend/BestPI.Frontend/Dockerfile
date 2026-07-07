FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS base
WORKDIR /app
EXPOSE 8080
ENV ASPNETCORE_URLS=http://0.0.0.0:8080
RUN apt-get update \
    && apt-get install -y --no-install-recommends libkrb5-3 \
    && rm -rf /var/lib/apt/lists/*

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY frontend/BestPI.Frontend/BestPI.Frontend.csproj frontend/BestPI.Frontend/
RUN dotnet restore frontend/BestPI.Frontend/BestPI.Frontend.csproj
COPY . .
WORKDIR /src/frontend/BestPI.Frontend
RUN dotnet publish -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
ENTRYPOINT ["dotnet", "BestPI.Frontend.dll"]
