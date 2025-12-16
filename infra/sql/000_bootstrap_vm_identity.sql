CREATE USER [vm-nba-runner] FROM EXTERNAL PROVIDER; ALTER ROLE db_ddladmin ADD MEMBER [vm-nba-runner]; ALTER ROLE db_datareader ADD MEMBER [vm-nba-runner]; ALTER ROLE db_datawriter ADD MEMBER 
[vm-nba-runner]; GO
