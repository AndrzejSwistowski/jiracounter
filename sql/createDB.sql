/*
    JIRA Changes Log Data Warehouse
    
    This script creates a database to store JIRA changes history in a data warehouse structure.
    
    The FactIssueHistory table contains the following columns:
    - Id (INT, primary key, auto increment)
    - HistoryId (INT, unique, identifies the history of the issue and prevents duplicates) 
    - HistoryDate (DATETIME, timestamp of the change)
    - AuthorId (INT, foreign key to DimUser dimension)
    - FactType (INT, type of change: 0 = create, 2 = transition, 3 = update)
    - IssueId (INT, identifier of the issue)
    - KeyId (INT, foreign key to DimIssueKey dimension)
    - TypeId (INT, foreign key to DimIssueType dimension)
    - StatusId (INT, foreign key to DimStatus dimension)
    - AssigneeId (INT, foreign key to DimUser dimension)
    - ReporterId (INT, foreign key to DimUser dimension)
    - AllocationId (INT, foreign key to DimAllocation dimension)
    - ProjectId (INT, foreign key to DimProject dimension)
    - ParentKeyId (INT, foreign key to the parent issue for subtasks)

    Allocation Types:
    - None: No allocation type assigned
    - NEW: New Development
    - IMPR: Improvement
    - PROD: Production
    - KTLO: Keep The Lights On
     allocation code contains only latin 4 characters 
     */

-- Create the database if it doesn't exist
IF NOT EXISTS (SELECT name FROM master.dbo.sysdatabases WHERE name = 'JiraWarehouse')
BEGIN
    CREATE DATABASE JiraWarehouse;
END
GO

USE JiraWarehouse;
GO

-- Create warehouse schema
IF NOT EXISTS (SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'warehouse')
BEGIN
    EXEC('CREATE SCHEMA warehouse');
END
GO

-- Create dimension tables
CREATE TABLE warehouse.DimProject (
    ProjectId INT IDENTITY(1,1) PRIMARY KEY,
    ProjectKey NVARCHAR(50) NOT NULL,
    ProjectName NVARCHAR(100) NOT NULL
);

CREATE TABLE warehouse.DimIssueType (
    TypeId INT IDENTITY(1,1) PRIMARY KEY,
    TypeName NVARCHAR(50) NOT NULL
);

CREATE TABLE warehouse.DimStatus (
    StatusId INT IDENTITY(1,1) PRIMARY KEY,
    StatusName NVARCHAR(50) NOT NULL
);

CREATE TABLE warehouse.DimUser (
    UserId INT IDENTITY(1,1) PRIMARY KEY,
    UserName NVARCHAR(100) NOT NULL,
    DisplayName NVARCHAR(100) NULL
);

CREATE TABLE warehouse.DimAllocation (
    AllocationId INT IDENTITY(1,1) PRIMARY KEY,
    AllocationCode CHAR(4) NOT NULL,
    AllocationName NVARCHAR(100) NOT NULL
);

CREATE TABLE warehouse.DimIssueKey (
    KeyId INT IDENTITY(1,1) PRIMARY KEY,
    IssueKey NVARCHAR(50) NOT NULL UNIQUE
);

-- Create the fact table for Jira issue history
CREATE TABLE warehouse.FactIssueHistory (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    HistoryId INT NOT NULL UNIQUE,
    HistoryDate DATETIME NOT NULL,
    FactType INT NOT NULL, -- 0 = create, 2 = transition, 3 = update,
    IssueId INT NOT NULL,
    KeyId INT FOREIGN KEY REFERENCES warehouse.DimIssueKey(KeyId),
    TypeId INT FOREIGN KEY REFERENCES warehouse.DimIssueType(TypeId),
    StatusId INT FOREIGN KEY REFERENCES warehouse.DimStatus(StatusId),
    AssigneeId INT FOREIGN KEY REFERENCES warehouse.DimUser(UserId),
    ReporterId INT FOREIGN KEY REFERENCES warehouse.DimUser(UserId),
    AllocationId INT FOREIGN KEY REFERENCES warehouse.DimAllocation(AllocationId),
    ProjectId INT FOREIGN KEY REFERENCES warehouse.DimProject(ProjectId),
    ParentKeyId INT NULL FOREIGN KEY REFERENCES warehouse.DimIssueKey(KeyId),
    AuthorId INT FOREIGN KEY REFERENCES warehouse.DimUser(UserId),
);

-- Create parameters table for ETL process
CREATE TABLE warehouse.Parameters (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    AgentName NVARCHAR(50) NOT NULL,
    ReadApiDateTo DATETIME NOT NULL,
    LastUpdated DATETIME DEFAULT GETDATE()
);

-- Create indices for better performance
CREATE INDEX IX_FactIssueHistory_HistoryDate ON warehouse.FactIssueHistory(HistoryDate);
CREATE INDEX IX_FactIssueHistory_IssueId ON warehouse.FactIssueHistory(IssueId);
CREATE INDEX IX_FactIssueHistory_KeyId ON warehouse.FactIssueHistory(KeyId);

-- Insert initial allocation values
INSERT INTO warehouse.DimAllocation (AllocationCode, AllocationName) 
VALUES
    ('NONE', 'No Allocation'), 
    ('NEW', 'New Development'),
    ('IMPR', 'Improvement'),
    ('PROD', 'Production'),
    ('KTLO', 'Keep The Lights On');