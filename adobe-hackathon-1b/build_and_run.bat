@echo off
echo Building Docker image for PDF Analysis System...
docker build -t document-intelligence .

IF %ERRORLEVEL% NEQ 0 (
    echo Error building Docker image. Exiting...
    exit /b %ERRORLEVEL%
)

echo.
echo Docker image built successfully!
echo.

IF "%~1"=="" (
    echo Running with default test case (Test case1)...
    docker run document-intelligence
) ELSE IF /I "%~1"=="all" (
    echo Running all test cases...
    docker run document-intelligence python test_system.py
) ELSE (
    echo Running with test case: %1
    docker run document-intelligence --test_case "%1"
)

echo.
echo Execution complete!