using GolfService.Entities;
using Microsoft.EntityFrameworkCore;
using System;

namespace GolfService.DbContexts
{
    public class ApplicationDbContext : DbContext
    {
        public DbSet<Round> Rounds { get; set; }
        public DbSet<Member> Members { get; set; }

        public ApplicationDbContext(DbContextOptions options): base(options) { }

        protected override void OnModelCreating(ModelBuilder builder)
        {
            base.OnModelCreating(builder);

            builder.Entity<Member>(b =>
            {
                b.Property(p => p.CreatedOn)
                    .HasConversion(t => t, t => DateTime.SpecifyKind(t, DateTimeKind.Utc));
            });
        }
    }
}
