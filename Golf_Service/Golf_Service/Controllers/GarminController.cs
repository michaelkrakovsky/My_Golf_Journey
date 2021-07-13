using System;
using Microsoft.AspNetCore.Mvc;
using GolfService.Services;

namespace GolfService.Controllers
{
    [ApiController]
    [Route("api/garmin")]
    public class GarminController : ControllerBase
    {
        private readonly IRoundRepository _roundRepository;

        public GarminController(IRoundRepository roundRepository)
        {
            _roundRepository = roundRepository ?? throw new ArgumentNullException(nameof(roundRepository));
        }

        [HttpPut("rounds")]
        public IActionResult UpdateGarminRounds()
        { 
            var garminRounds = _roundRepository.UpdateGarminRounds();
            return Ok(garminRounds);
        }
    }
}
