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

GO

-- Create stored procedures for ETL operations
-- ==========================================

-- Procedure: GetOrInsertProject
-- Purpose: Retrieves ProjectId for a given project key/name, or inserts if not exists
CREATE OR ALTER PROCEDURE warehouse.GetOrInsertProject
    @ProjectKey NVARCHAR(50),
    @ProjectName NVARCHAR(100),
    @ProjectId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT @ProjectId = ProjectId 
    FROM warehouse.DimProject 
    WHERE ProjectKey = @ProjectKey;
    
    IF @ProjectId IS NULL
    BEGIN
        INSERT INTO warehouse.DimProject (ProjectKey, ProjectName)
        VALUES (@ProjectKey, @ProjectName);
        
        SET @ProjectId = SCOPE_IDENTITY();
    END
END;
GO

-- Procedure: GetOrInsertIssueType
-- Purpose: Retrieves TypeId for a given issue type, or inserts if not exists
CREATE OR ALTER PROCEDURE warehouse.GetOrInsertIssueType
    @TypeName NVARCHAR(50),
    @TypeId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT @TypeId = TypeId 
    FROM warehouse.DimIssueType 
    WHERE TypeName = @TypeName;
    
    IF @TypeId IS NULL
    BEGIN
        INSERT INTO warehouse.DimIssueType (TypeName)
        VALUES (@TypeName);
        
        SET @TypeId = SCOPE_IDENTITY();
    END
END;
GO

-- Procedure: GetOrInsertStatus
-- Purpose: Retrieves StatusId for a given status name, or inserts if not exists
CREATE OR ALTER PROCEDURE warehouse.GetOrInsertStatus
    @StatusName NVARCHAR(50),
    @StatusId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT @StatusId = StatusId 
    FROM warehouse.DimStatus 
    WHERE StatusName = @StatusName;
    
    IF @StatusId IS NULL
    BEGIN
        INSERT INTO warehouse.DimStatus (StatusName)
        VALUES (@StatusName);
        
        SET @StatusId = SCOPE_IDENTITY();
    END
END;
GO

-- Procedure: GetOrInsertUser
-- Purpose: Retrieves UserId for a given username, or inserts if not exists
CREATE OR ALTER PROCEDURE warehouse.GetOrInsertUser
    @UserName NVARCHAR(100),
    @DisplayName NVARCHAR(100) = NULL,
    @UserId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT @UserId = UserId 
    FROM warehouse.DimUser 
    WHERE UserName = @UserName;
    
    IF @UserId IS NULL
    BEGIN
        INSERT INTO warehouse.DimUser (UserName, DisplayName)
        VALUES (@UserName, @DisplayName);
        
        SET @UserId = SCOPE_IDENTITY();
    END
    ELSE IF @DisplayName IS NOT NULL
    BEGIN
        -- Update display name if provided
        UPDATE warehouse.DimUser
        SET DisplayName = @DisplayName
        WHERE UserId = @UserId;
    END
END;
GO

-- Procedure: GetOrInsertAllocation
-- Purpose: Retrieves AllocationId for a given allocation code, or returns the default if invalid
CREATE OR ALTER PROCEDURE warehouse.GetOrInsertAllocation
    @AllocationCode CHAR(4),
    @AllocationId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @AllocationCode IS NULL OR @AllocationCode = ''
    BEGIN
        -- Return default 'NONE' allocation
        SELECT @AllocationId = AllocationId 
        FROM warehouse.DimAllocation 
        WHERE AllocationCode = 'NONE';
    END
    ELSE
    BEGIN
        SELECT @AllocationId = AllocationId 
        FROM warehouse.DimAllocation 
        WHERE AllocationCode = @AllocationCode;
        
        -- If not found, return default 'NONE' allocation
        IF @AllocationId IS NULL
        BEGIN
            SELECT @AllocationId = AllocationId 
            FROM warehouse.DimAllocation 
            WHERE AllocationCode = 'NONE';
        END
    END
END;
GO

-- Procedure: GetOrInsertIssueKey
-- Purpose: Retrieves KeyId for a given issue key, or inserts if not exists
CREATE OR ALTER PROCEDURE warehouse.GetOrInsertIssueKey
    @IssueKey NVARCHAR(50),
    @KeyId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT @KeyId = KeyId 
    FROM warehouse.DimIssueKey 
    WHERE IssueKey = @IssueKey;
    
    IF @KeyId IS NULL
    BEGIN
        INSERT INTO warehouse.DimIssueKey (IssueKey)
        VALUES (@IssueKey);
        
        SET @KeyId = SCOPE_IDENTITY();
    END
END;
GO

-- Procedure: InsertIssueHistory
-- Purpose: Inserts a new issue history record, handling all dimension lookups
CREATE OR ALTER PROCEDURE warehouse.InsertIssueHistory
    @HistoryId INT,
    @HistoryDate DATETIME,
    @FactType INT,
    @IssueId INT,
    @IssueKey NVARCHAR(50),
    @TypeName NVARCHAR(50),
    @StatusName NVARCHAR(50),
    @AssigneeUserName NVARCHAR(100) = NULL,
    @AssigneeDisplayName NVARCHAR(100) = NULL,
    @ReporterUserName NVARCHAR(100) = NULL,
    @ReporterDisplayName NVARCHAR(100) = NULL,
    @AllocationCode CHAR(4) = NULL,
    @ProjectKey NVARCHAR(50),
    @ProjectName NVARCHAR(100),
    @ParentKey NVARCHAR(50) = NULL,
    @AuthorUserName NVARCHAR(100),
    @AuthorDisplayName NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @KeyId INT, @TypeId INT, @StatusId INT, @AssigneeId INT, @ReporterId INT,
            @AllocationId INT, @ProjectId INT, @ParentKeyId INT, @AuthorId INT;
    
    -- Check if this history record already exists
    IF EXISTS (SELECT 1 FROM warehouse.FactIssueHistory WHERE HistoryId = @HistoryId)
        RETURN;
    
    -- Get or insert all dimension values
    EXEC warehouse.GetOrInsertIssueKey @IssueKey, @KeyId OUTPUT;
    EXEC warehouse.GetOrInsertIssueType @TypeName, @TypeId OUTPUT;
    EXEC warehouse.GetOrInsertStatus @StatusName, @StatusId OUTPUT;
    EXEC warehouse.GetOrInsertUser @AuthorUserName, @AuthorDisplayName, @AuthorId OUTPUT;
    EXEC warehouse.GetOrInsertProject @ProjectKey, @ProjectName, @ProjectId OUTPUT;
    
    -- Optional dimensions with NULL handling
    IF @AssigneeUserName IS NOT NULL
        EXEC warehouse.GetOrInsertUser @AssigneeUserName, @AssigneeDisplayName, @AssigneeId OUTPUT;
    
    IF @ReporterUserName IS NOT NULL
        EXEC warehouse.GetOrInsertUser @ReporterUserName, @ReporterDisplayName, @ReporterId OUTPUT;
    
    EXEC warehouse.GetOrInsertAllocation @AllocationCode, @AllocationId OUTPUT;
    
    IF @ParentKey IS NOT NULL
        EXEC warehouse.GetOrInsertIssueKey @ParentKey, @ParentKeyId OUTPUT;
    
    -- Insert the fact record
    INSERT INTO warehouse.FactIssueHistory (
        HistoryId, HistoryDate, FactType, IssueId, KeyId, TypeId, StatusId,
        AssigneeId, ReporterId, AllocationId, ProjectId, ParentKeyId, AuthorId
    )
    VALUES (
        @HistoryId, @HistoryDate, @FactType, @IssueId, @KeyId, @TypeId, @StatusId,
        @AssigneeId, @ReporterId, @AllocationId, @ProjectId, @ParentKeyId, @AuthorId
    );
END;
GO

-- Procedure: UpdateETLParameters
-- Purpose: Updates the ETL process tracking parameters
CREATE OR ALTER PROCEDURE warehouse.UpdateETLParameters
    @AgentName NVARCHAR(50),
    @ReadApiDateTo DATETIME
AS
BEGIN
    SET NOCOUNT ON;
    
    IF EXISTS (SELECT 1 FROM warehouse.Parameters WHERE AgentName = @AgentName)
    BEGIN
        UPDATE warehouse.Parameters
        SET ReadApiDateTo = @ReadApiDateTo,
            LastUpdated = GETDATE()
        WHERE AgentName = @AgentName;
    END
    ELSE
    BEGIN
        INSERT INTO warehouse.Parameters (AgentName, ReadApiDateTo)
        VALUES (@AgentName, @ReadApiDateTo);
    END
END;
GO

-- Procedure: GetETLParameters
-- Purpose: Retrieves the ETL process tracking parameters for a specific agent
CREATE OR ALTER PROCEDURE warehouse.GetETLParameters
    @AgentName NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT ReadApiDateTo, LastUpdated
    FROM warehouse.Parameters
    WHERE AgentName = @AgentName;
END;
GO

-- Procedure: GetLastImportedIssueDate
-- Purpose: Returns the date of the last imported issue history record
CREATE OR ALTER PROCEDURE warehouse.GetLastImportedIssueDate
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT TOP 1 HistoryDate
    FROM warehouse.FactIssueHistory
    ORDER BY HistoryDate DESC;
END;
GO

-- Procedure: GetIssueHistorySummary
-- Purpose: Retrieves summary statistics about issue history
CREATE OR ALTER PROCEDURE warehouse.GetIssueHistorySummary
    @StartDate DATETIME = NULL,
    @EndDate DATETIME = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @StartDate IS NULL
        SET @StartDate = DATEADD(DAY, -30, GETDATE());
    
    IF @EndDate IS NULL
        SET @EndDate = GETDATE();
    
    SELECT 
        COUNT(*) AS TotalRecords,
        MIN(HistoryDate) AS OldestRecord,
        MAX(HistoryDate) AS NewestRecord,
        COUNT(DISTINCT IssueId) AS UniqueIssues,
        COUNT(DISTINCT ProjectId) AS UniqueProjects
    FROM warehouse.FactIssueHistory
    WHERE HistoryDate BETWEEN @StartDate AND @EndDate;
END;
GO