using GolfService.Entities;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Options;

namespace GolfService.Properties
{
    public class UserSignInManager : SignInManager<Member>
    {
        public UserSignInManager(UserManager<Member> userManager, IHttpContextAccessor contextAccessor, IUserClaimsPrincipalFactory<Member> claimsFactory, IOptions<IdentityOptions> optionsAccessor, ILogger<SignInManager<Member>> logger, IAuthenticationSchemeProvider schemes, IUserConfirmation<Member> confirmation)
            : base(userManager, contextAccessor, claimsFactory, optionsAccessor, logger, schemes, confirmation)
        {
        }

        public override async Task<SignInResult> PasswordSignInAsync(Member user, string password, bool isPersistent, bool lockoutOnFailure)
        {
            // Ability to add active here - var isActive = user.AccountStatusId == UserAccountStatus.Active;
            var passwordSignInResult = await base.PasswordSignInAsync(user, password, isPersistent, lockoutOnFailure);
            return true ? passwordSignInResult : SignInResult.NotAllowed;
        }

        public override Task SignOutAsync()
        {
            return base.SignOutAsync();
        }
    }
}