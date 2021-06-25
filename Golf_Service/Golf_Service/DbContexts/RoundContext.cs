using System;
using Microsoft.EntityFrameworkCore;
using GolfService.Entities;

namespace GolfService.DbContexts
{
    public class RoundContext : DbContext
    {
        public RoundContext(DbContextOptions<RoundContext> options)
            : base(options)
        {

        }
        public DbSet<Round> Rounds { get; set; }
    }
}
