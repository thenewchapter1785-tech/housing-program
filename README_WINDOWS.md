# Windows setup guide

1. Install Python 3.12 from https://www.python.org/downloads/windows/
2. Install MySQL Server or MariaDB locally.
3. Create a database named housing_app.
4. Set environment variables in PowerShell:
   ```powershell
   $env:MYSQL_HOST = "localhost"
   $env:MYSQL_PORT = "3306"
   $env:MYSQL_USER = "root"
   $env:MYSQL_PASSWORD = "your_password"
   $env:MYSQL_DATABASE = "housing_app"
   ```
5. Run the app:
   ```powershell
   .\run_app.bat
   ```

The app will prompt you to sign in or create an account, then run searches and store results in MySQL.
