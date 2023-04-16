using Microsoft.AspNetCore.DataProtection;
using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Options;

namespace GolfService.Entities
{
    public class CustomEmailTokenProvider<TUser> : DataProtectorTokenProvider<TUser> where TUser : class
    {
        public CustomEmailTokenProvider(IDataProtectionProvider dataProtectionProvider, IOptions<EmailConfirmationTokenProviderOptions> options, ILogger<DataProtectorTokenProvider<TUser>> logger)
            : base(dataProtectionProvider, options, logger)
        {
        }
    }

    public class EmailConfirmationTokenProviderOptions : DataProtectionTokenProviderOptions
    {
        public EmailConfirmationTokenProviderOptions()
        {
            Name = "CustomEmailTokenProvider";
            TokenLifespan = TimeSpan.FromDays(1);
        }
    }
}
