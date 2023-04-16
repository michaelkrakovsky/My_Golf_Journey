using System;
using OpenIddict.Abstractions;
using static OpenIddict.Abstractions.OpenIddictConstants;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using GolfService.DbContexts;
using Microsoft.EntityFrameworkCore;
using System.Threading;

namespace GolfService
{
    public class Worker : IHostedService
    {
        public static string INTERNAL_CLIENT_ID = "XXXXE";
        public static string HUB_CLIENT_ID = "XXXXXE";

        private readonly IServiceProvider _serviceProvider;

        public Worker(IServiceProvider serviceProvider)
            => _serviceProvider = serviceProvider;

        public async Task StartAsync(CancellationToken cancellationToken)
        {
            using var scope = _serviceProvider.CreateScope();

            var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();

            var manager = scope.ServiceProvider.GetRequiredService<IOpenIddictApplicationManager>();

            if (await manager.FindByClientIdAsync(HUB_CLIENT_ID) is null)
            {
                await manager.CreateAsync(new OpenIddictApplicationDescriptor
                {
                    ClientId = HUB_CLIENT_ID,
                    DisplayName = "Hub Client",
                    Permissions =
                    {
                        Permissions.Endpoints.Token,
                        Permissions.Endpoints.Logout,
                        Permissions.GrantTypes.RefreshToken,
                        Permissions.GrantTypes.Password,
                        Permissions.Scopes.Email,
                        Permissions.Scopes.Profile,
                        Permissions.Scopes.Roles
                    }
                });
            }

            if (await manager.FindByClientIdAsync(INTERNAL_CLIENT_ID) is null)
            {
                await manager.CreateAsync(new OpenIddictApplicationDescriptor
                {
                    ClientId = INTERNAL_CLIENT_ID,
                    ClientSecret = "42C432E4-4896-425D-A5CE-4716D7583F04",
                    DisplayName = "Internal",
                    Permissions =
                    {
                        Permissions.Endpoints.Token,
                        Permissions.Endpoints.Logout,
                        Permissions.GrantTypes.RefreshToken,
                        Permissions.GrantTypes.ClientCredentials,
                        Permissions.Scopes.Email,
                        Permissions.Scopes.Profile,
                        Permissions.Scopes.Roles
                    }
                });
            }
        }

        public Task StopAsync(CancellationToken cancellationToken) => Task.CompletedTask;
    }

    public class Startup
    {
        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        public IConfiguration Configuration { get; }

        // This method gets called by the runtime. Use this method to add services to the container.
        public void ConfigureServices(IServiceCollection services)
        {
            services.AddControllersWithViews();

            services.AddDbContext<ApplicationDbContext>(options =>
            {
                // Configure Entity Framework Core to use Microsoft SQL Server.
                options.UseSqlServer(Configuration.GetConnectionString("DefaultConnection"));

                // Register the entity sets needed by OpenIddict.
                // Note: use the generic overload if you need to replace the default OpenIddict entities.
                options.UseOpenIddict();
            });

            services.AddOpenIddict()

                // Register the OpenIddict core components.
                .AddCore(options =>
                {
                    // Configure OpenIddict to use the Entity Framework Core stores and models.
                    // Note: call ReplaceDefaultEntities() to replace the default entities.
                    options.UseEntityFrameworkCore()
                           .UseDbContext<ApplicationDbContext>();
                })

                // Register the OpenIddict server components.
                .AddServer(options =>
                {
                    // Enable the token endpoint.
                    options.SetTokenEndpointUris("connect/token");

                    // Enable the client credentials flow.
                    options.AllowClientCredentialsFlow();

                    // Register the signing and encryption credentials.
                    options.AddDevelopmentEncryptionCertificate()
                           .AddDevelopmentSigningCertificate();

                    // Register the ASP.NET Core host and configure the ASP.NET Core options.
                    options.UseAspNetCore()
                           .EnableTokenEndpointPassthrough();
                })

                // Register the OpenIddict validation components.
                .AddValidation(options =>
                {
                    // Import the configuration from the local OpenIddict server instance.
                    options.UseLocalServer();

                    // Register the ASP.NET Core host.
                    options.UseAspNetCore();
                });

            // Register the worker responsible of seeding the database with the sample clients.
            // Note: in a real world application, this step should be part of a setup script.
            services.AddHostedService<Worker>();

            services.AddControllers();
        }

        // This method gets called by the runtime. Use this method to configure the HTTP request pipeline.
        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }

            app.UseHttpsRedirection();

            app.UseRouting();

            app.UseAuthorization();

            app.UseEndpoints(endpoints =>
            {
                endpoints.MapControllers();
            });
        }
    }
}
