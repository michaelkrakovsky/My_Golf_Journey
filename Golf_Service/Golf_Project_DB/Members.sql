CREATE TABLE [dbo].[Members]
(
	[Id] UNIQUEIDENTIFIER NOT NULL PRIMARY KEY, 
    [FirstName] NVARCHAR(50) NOT NULL, 
    [LastName] NCHAR(50) NOT NULL, 
    [Email] NVARCHAR(MAX) NOT NULL, 
    [CreatedOn] DATETIME2 NOT NULL, 
    [PasswordHash] NVARCHAR(50) NULL, 
    [SecurityStamp] NVARCHAR(50) NULL, 
    [LockoutEndDateUtc] DATETIME2 NULL, 
    [LockoutEnabled] BIT NOT NULL, 
    [AccessFailedCount] INT NOT NULL
)
