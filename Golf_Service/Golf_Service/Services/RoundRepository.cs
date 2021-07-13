using System;
using GolfService.Entities;
using GolfService.DbContexts;
using GolfService.Services;
using System.Linq;
using System.Collections.Generic;

namespace GolfService.Services
{
    public class RoundRepository : IRoundRepository
    {
        private readonly RoundContext _context;

        public RoundRepository(RoundContext context)
        {
            _context = context ?? throw new ArgumentNullException(nameof(context));
        }

        public int UpdateGarminRounds()
        {
            return 2;
        }
    }
}
