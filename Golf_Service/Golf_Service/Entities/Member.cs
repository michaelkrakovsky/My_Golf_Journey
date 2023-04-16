using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace GolfService.Entities
{
    [Table("Members", Schema = "dbo")]
    public class Member
    {
        [Key]
        public Guid Id { get; set; }
        public string FirstName { get; set; }
        public string LastName { get; set; }
        public string Email { get; set; }
        public DateTime CreatedOn { get; set; }
        public string PasswordHash { get; set; }
        public string SecurityStamp { get; set; }
        public DateTime LockEndDateUtc { get; set; }
        public bool LockoutEnabled { get; set; }
        public int AccessFailedCount { get; set; }
    }
}
