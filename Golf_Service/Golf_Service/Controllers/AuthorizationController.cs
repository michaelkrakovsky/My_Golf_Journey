using GolfService;
using GolfService.Entities;
using Microsoft.AspNetCore;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;
using OpenIddict.Abstractions;
using OpenIddict.EntityFrameworkCore.Models;
using OpenIddict.Server.AspNetCore;
using System.Collections.Immutable;
using System.Security.Claims;
using static OpenIddict.Abstractions.OpenIddictConstants;

namespace Platform.Users.Controllers
{
    [ApiExplorerSettings(IgnoreApi = true)]
    public class AuthorizationController : Controller
    {
        private readonly SignInManager<Member> signInManager;
        private readonly UserManager<Member> userManager;
        private readonly IOpenIddictTokenManager tokenManager;
        private readonly IOpenIddictApplicationManager applicationManager;

        public AuthorizationController
        (
            SignInManager<Member> signInManager,
            IOptionsSnapshot<UserManagerWithOptions<Member>> userManager,
            IOpenIddictTokenManager tokenManager,
            IOpenIddictApplicationManager applicationManager
        )
        {
            this.signInManager = signInManager;
            this.userManager = userManager.Value.UserManager;
            this.tokenManager = tokenManager;
            this.applicationManager = applicationManager;
        }

        [HttpGet("~/connect/logout")]
        public async Task<IActionResult> Logout()
        {
            var authResult = await HttpContext.AuthenticateAsync(OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);

            // Ask ASP.NET Core Identity to delete the local and external cookies created
            // when the user agent is redirected from the external identity provider
            // after a successful authentication flow (e.g Google or Facebook).
            await HttpContext.SignOutAsync(OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
            if (authResult.Principal != null)
            {
                var claim = authResult.Principal.GetClaim(Claims.Subject);
                var tokens = tokenManager.FindBySubjectAsync(claim ?? string.Empty);
                await foreach (var token in tokens)
                {
                    var status = ((OpenIddictEntityFrameworkCoreToken<string, OpenIddictEntityFrameworkCoreApplication, OpenIddictEntityFrameworkCoreAuthorization>)token).Status;
                    if (status != "revoked")
                    {
                        await tokenManager.TryRevokeAsync(token);
                    }
                }
            }

            // Returning a SignOutResult will ask OpenIddict to redirect the user agent
            // to the post_logout_redirect_uri specified by the client application or to
            // the RedirectUri specified in the authentication properties if none was set.
            return SignOut(authenticationSchemes: OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
        }

        [HttpPost("~/connect/token"), IgnoreAntiforgeryToken, Produces("application/json")]
        public async Task<IActionResult> Exchange()
        {
            var request = HttpContext.GetOpenIddictServerRequest();
            if (request != null && request.IsPasswordGrantType() && request.ClientId == Worker.HUB_CLIENT_ID)
            {
                return await PasswordGrantFlow(request);
            }
            else if (request != null && request.IsRefreshTokenGrantType() && request.ClientId == Worker.HUB_CLIENT_ID)
            {
                return await RefreshTokenGrantFlow();
            }
            else if (request != null && request.IsClientCredentialsGrantType() && request.ClientId == Worker.INTERNAL_CLIENT_ID)
            {
                return await ClientCrendentialsGrantFlow(request);
            }
            throw new NotImplementedException("The specified grant type is not implemented.");
        }

        private async Task<IActionResult> RefreshTokenGrantFlow()
        {
            // Retrieve the claims principal stored in the refresh token.
            var result = await HttpContext.AuthenticateAsync(OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);

            if (!result.Succeeded || result.Principal == null)
            {
                var properties = new AuthenticationProperties(new Dictionary<string, string?>
                {
                    [OpenIddictServerAspNetCoreConstants.Properties.Error] = Errors.InvalidGrant,
                    [OpenIddictServerAspNetCoreConstants.Properties.ErrorDescription] = "The refresh token is no longer valid."
                });

                return Forbid(properties, OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
            }

            // Retrieve the user profile corresponding to the refresh token.
            var user = await userManager.FindByIdAsync(result.Principal.GetClaim(Claims.Subject)!);
            if (user == null)
            {
                var properties = new AuthenticationProperties(new Dictionary<string, string?>
                {
                    [OpenIddictServerAspNetCoreConstants.Properties.Error] = Errors.InvalidGrant,
                    [OpenIddictServerAspNetCoreConstants.Properties.ErrorDescription] = "The refresh token is no longer valid."
                });

                return Forbid(properties, OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
            }

            // Ensure the user is still allowed to sign in.
            if (!await signInManager.CanSignInAsync(user))
            {
                var properties = new AuthenticationProperties(new Dictionary<string, string?>
                {
                    [OpenIddictServerAspNetCoreConstants.Properties.Error] = Errors.InvalidGrant,
                    [OpenIddictServerAspNetCoreConstants.Properties.ErrorDescription] = "The user is no longer allowed to sign in."
                });

                return Forbid(properties, OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
            }

            var identity = new ClaimsIdentity(result.Principal.Claims,
                authenticationType: TokenValidationParameters.DefaultAuthenticationType,
                nameType: Claims.Name,
                roleType: Claims.Role
            );

            // Override the user claims present in the principal in case they changed since the refresh token was issued.
            identity.SetClaim(Claims.Subject, user.Id.ToString())
                    .SetClaim(Claims.Email, user.Email)
                    .SetClaim(Claims.GivenName, user.FirstName)
                    .SetClaim(Claims.FamilyName, user.LastName)
                    .SetClaim("Environment", "TODO")
                    .SetClaims(Claims.Role, result.Principal.IsInRole("System") ? ImmutableArray.Create("System") : (await userManager.GetRolesAsync(user)).ToImmutableArray());

            identity.SetDestinations(GetDestinations);

            return SignIn(new ClaimsPrincipal(identity), OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
        }

        private async Task<IActionResult> PasswordGrantFlow(OpenIddictRequest request)
        {
            if (request.Username == null)
            {
                ModelState.AddModelError(nameof(request.Username), "Required field username not provided.");
                return BadRequest(ModelState);
            }

            if (request.Password == null)
            {
                ModelState.AddModelError(nameof(request.Password), "Required field password not provided.");
                return BadRequest(ModelState);
            }

            var user = await userManager.FindByNameAsync(request.Username);
            if (user == null)
            {
                var properties = new AuthenticationProperties(new Dictionary<string, string?>
                {
                    [OpenIddictServerAspNetCoreConstants.Properties.Error] = Errors.InvalidGrant,
                    [OpenIddictServerAspNetCoreConstants.Properties.ErrorDescription] =
                        "The username/password combination is invalid."
                });

                return Forbid(properties, OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
            }

            // Validate the username/password parameters and ensure the account is not locked out.
            var result = await signInManager.CheckPasswordSignInAsync(user, request.Password, lockoutOnFailure: true);
            if (!result.Succeeded)
            {
                var properties = new AuthenticationProperties(new Dictionary<string, string?>
                {
                    [OpenIddictServerAspNetCoreConstants.Properties.Error] = Errors.InvalidGrant,
                    [OpenIddictServerAspNetCoreConstants.Properties.ErrorDescription] =
                        "The username/password combination is invalid."
                });

                return Forbid(properties, OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
            }

            // Create the claims-based identity that will be used by OpenIddict to generate tokens.
            var identity = new ClaimsIdentity
            (
                authenticationType: TokenValidationParameters.DefaultAuthenticationType,
                nameType: Claims.Name,
                roleType: Claims.Role
            );

            // Add the claims that will be persisted in the tokens.
            identity.SetClaim(Claims.Subject, user.Id.ToString())
                    .SetClaim(Claims.Email, user.Email)
                    .SetClaim(Claims.GivenName, user.FirstName)
                    .SetClaim(Claims.FamilyName, user.LastName)
                    .SetClaim("Environment", "TODO")
                    .SetClaims(Claims.Role, (await userManager.GetRolesAsync(user)).ToImmutableArray());

            // Set the list of scopes granted to the client application.
            identity.SetScopes(new[]
            {
                    Scopes.OpenId,
                    Scopes.Email,
                    Scopes.Profile,
                    Scopes.Roles,
                    Scopes.OfflineAccess
                }.Intersect(request.GetScopes()));

            identity.SetDestinations(GetDestinations);

            return SignIn(new ClaimsPrincipal(identity), OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
        }

        private async Task<IActionResult> ClientCrendentialsGrantFlow(OpenIddictRequest request)
        {
            // Note: the client credentials are automatically validated by OpenIddict:
            // if client_id or client_secret are invalid, this action won't be invoked.

            var application = await applicationManager.FindByClientIdAsync(request.ClientId!);
            if (application == null)
            {
                throw new InvalidOperationException("The application details cannot be found in the database.");
            }

            var user = await userManager.FindByNameAsync("system.user@ezra.com");
            if (user == null)
            {
                var properties = new AuthenticationProperties(new Dictionary<string, string?>
                {
                    [OpenIddictServerAspNetCoreConstants.Properties.Error] = Errors.InvalidGrant,
                    [OpenIddictServerAspNetCoreConstants.Properties.ErrorDescription] =
                        "User cannot be found."
                });

                return Forbid(properties, OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
            }

            // Create the claims-based identity that will be used by OpenIddict to generate tokens.
            var identity = new ClaimsIdentity
            (
                authenticationType: TokenValidationParameters.DefaultAuthenticationType,
                nameType: Claims.Name,
                roleType: Claims.Role
            );

            var clientId = await applicationManager.GetClientIdAsync(application);
            var displayName = await applicationManager.GetDisplayNameAsync(application);
            // Add the claims that will be persisted in the tokens.
            identity.SetClaim(Claims.Subject, user.Id.ToString())
                    .SetClaim("obo", $"{displayName}-{clientId}")
                    .SetClaim(Claims.Email, user.Email)
                    .SetClaim(Claims.GivenName, user.FirstName)
                    .SetClaim(Claims.FamilyName, user.LastName)
                    .SetClaim("Environment", "TODO")
                    .SetClaims(Claims.Role, ImmutableArray.Create("System"));

            // Note: In the original OAuth 2.0 specification, the client credentials grant
            // doesn't return an identity token, which is an OpenID Connect concept.
            //
            // As a non-standardized extension, OpenIddict allows returning an id_token
            // to convey information about the client application when the "openid" scope
            // is granted (i.e specified when calling principal.SetScopes()). When the "openid"
            // scope is not explicitly set, no identity token is returned to the client application.
            identity.SetScopes(Array.Empty<string>().Intersect(request.GetScopes()));
            identity.SetDestinations(GetDestinations);

            return SignIn(new ClaimsPrincipal(identity), OpenIddictServerAspNetCoreDefaults.AuthenticationScheme);
        }

        private static IEnumerable<string> GetDestinations(Claim claim)
        {
            if (claim.Subject == null) yield break;
            // Note: by default, claims are NOT automatically included in the access and identity tokens.
            // To allow OpenIddict to serialize them, you must attach them a destination, that specifies
            // whether they should be included in access tokens, in identity tokens or in both.
            switch (claim.Type)
            {
                case Claims.Name:
                    yield return Destinations.AccessToken;

                    if (claim.Subject.HasScope(Scopes.Profile))
                        yield return Destinations.IdentityToken;

                    yield break;

                case Claims.Email:
                    yield return Destinations.AccessToken;

                    if (claim.Subject.HasScope(Scopes.Email))
                        yield return Destinations.IdentityToken;

                    yield break;

                case Claims.Role:
                    yield return Destinations.AccessToken;

                    if (claim.Subject.HasScope(Scopes.Roles))
                        yield return Destinations.IdentityToken;

                    yield break;

                // Never include the security stamp in the access and identity tokens, as it's a secret value.
                case "AspNet.Identity.SecurityStamp": yield break;

                default:
                    yield return Destinations.AccessToken;
                    yield return Destinations.IdentityToken;
                    yield break;
            }
        }
    }
}
