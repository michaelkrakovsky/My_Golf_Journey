using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Options;

namespace GolfService.Entities
{
    public class UserManagerWithOptions<T>
        where T : class
    {
        public UserManager<T> UserManager { get; set; } = null!;
    }
    public class UserManagerConfiguration<T> : IConfigureOptions<UserManagerWithOptions<T>>
        where T : class
    {
        private readonly UserManager<T> UserManager;

        public UserManagerConfiguration(UserManager<T> UserManager, CustomEmailTokenProvider<T> TokenProvider)
        {
            UserManager.RegisterTokenProvider(TokenOptions.DefaultProvider, TokenProvider);
            this.UserManager = UserManager;
        }

        public void Configure(UserManagerWithOptions<T> options)
        {
            options.UserManager = UserManager;
        }
    }
}