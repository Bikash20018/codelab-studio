@echo off
setlocal
title Package CodeLab Studio as MSIX
cd /d "%~dp0"

rem   make_msix.bat [version] [testsign]
rem     version   defaults to 2.1.0 - must match the dist\<version>\ folder
rem               build.bat produced and the manifest's four-part Version.
rem     testsign  OPTIONAL, local testing only - see section 6 at the bottom.

set "VERSION=2.1.0"
set "TESTSIGN="
for %%a in (%*) do (
  if /i "%%a"=="testsign" (set "TESTSIGN=1") else (set "VERSION=%%a")
)
set "MSIXVER=%VERSION%.0"
set "PAYLOAD=dist\%VERSION%\CodeLabStudio"
set "LAYOUT=msix\layout"
set "MANIFEST=packaging\AppxManifest.xml"
set "PACKAGE=installer\CodeLabStudio-%MSIXVER%-x64.msix"

echo [1/7] Checking inputs (version %VERSION%, manifest Version %MSIXVER%)...
if not exist "%PAYLOAD%\CodeLabStudio.exe" (
  echo   Not found: %PAYLOAD%\CodeLabStudio.exe
  echo   Run build.bat first and make sure its output is in dist\%VERSION%\CodeLabStudio.
  goto :fail
)
if not exist "assets\msix\StoreLogo.png" (
  echo   Not found: assets\msix\StoreLogo.png
  echo   Run:  python make_assets.py
  goto :fail
)
findstr /r /c:"Version=.%MSIXVER%." "%MANIFEST%" >nul || (
  echo   %MANIFEST% does not say Version="%MSIXVER%".
  echo   The Store compares the manifest version, not the folder name - fix one of them.
  echo   Reminder: four parts, and the fourth MUST be 0.
  goto :fail
)
findstr /c:"PLACEHOLDER" "%MANIFEST%" >nul && (
  echo   WARNING: %MANIFEST% still contains PLACEHOLDER identity values.
  echo   The package will build and can be test-installed, but Partner Center
  echo   will reject the upload. Replace Name, Publisher and PublisherDisplayName
  echo   from Partner Center ^> Product management ^> Product identity.
)

if not exist "licenses\THIRD-PARTY-NOTICES.txt" (
  echo   Not found: licenses\THIRD-PARTY-NOTICES.txt
  echo   The GPL requires the bundled compiler's licence texts to ship with it.
  goto :fail
)
if not exist "installer" mkdir "installer"

echo [2/7] Locating the Windows SDK...
set "SDKROOT=%ProgramFiles(x86)%\Windows Kits\10\bin"
if not exist "%SDKROOT%" set "SDKROOT=%ProgramFiles%\Windows Kits\10\bin"
set "SDKBIN="
rem Keep this on one line: the SDK path contains "(x86)", and a parenthesised
rem do-block would end at that bracket instead of at the block's own.
rem The newest matching folder wins because /d walks them in name order.
for /d %%d in ("%SDKROOT%\10.*") do if exist "%%~fd\x64\makeappx.exe" set "SDKBIN=%%~fd\x64"
if not defined SDKBIN (
  echo   makeappx.exe was not found under "%SDKROOT%".
  echo   Install the Windows 10/11 SDK ^(the "Windows SDK Signing Tools" component
  echo   is enough^): https://developer.microsoft.com/windows/downloads/windows-sdk/
  goto :fail
)
echo   Using "%SDKBIN%"

echo [3/7] Staging the package layout in %LAYOUT% ...
rem /MIR wipes anything left over from the previous run, including the manifest
rem and Assets - both are re-copied right below.
robocopy "%PAYLOAD%" "%LAYOUT%" /MIR /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto :fail
copy /Y "%MANIFEST%" "%LAYOUT%\AppxManifest.xml" >nul || goto :fail
robocopy "assets\msix" "%LAYOUT%\Assets" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto :fail
rem The licence texts also ride inside _internal\licenses (Help > Licences reads
rem them there); this copy just puts them where a person can find them.
robocopy "licenses" "%LAYOUT%\licenses" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto :fail

echo [4/7] Removing toolchain parts the IDE never runs...
rem Store policy 10.2.3: do not ship secondary software the product does not use.
rem This only touches the staged copy - dist\ and the Inno installer keep the
rem complete WinLibs kit.
python prune_toolchain.py "%LAYOUT%" || goto :fail

echo [5/7] Verifying the pruned toolchain still builds and debugs...
python verify_toolchain.py "%LAYOUT%" || goto :fail

echo [6/7] Building resources.pri (indexes every payload file - this is slow)...
if not exist "%SDKBIN%\makepri.exe" (
  rem Quote it: the SDK path holds "(x86)", which would close this block early.
  echo   makepri.exe is missing from "%SDKBIN%" - reinstall the SDK.
  goto :fail
)
rem priconfig.xml lives outside the layout so it is not packed into the MSIX.
"%SDKBIN%\makepri.exe" createconfig /cf "msix\priconfig.xml" /dq en-US /o || goto :fail
"%SDKBIN%\makepri.exe" new /pr "%LAYOUT%" /cf "msix\priconfig.xml" ^
  /mn "%LAYOUT%\AppxManifest.xml" /of "%LAYOUT%\resources.pri" /o || goto :fail

echo [7/7] Packing %PACKAGE% ...
rem No /nv: the semantic validation is the point. Default block map hash is
rem SHA256, which is what the Store requires - do not pass /h.
"%SDKBIN%\makeappx.exe" pack /o /d "%LAYOUT%" /p "%PACKAGE%" || goto :fail

echo.
echo Done:  %PACKAGE%
echo Upload that file to Partner Center ^> your app ^> Packages. It does NOT need
echo to be signed: the Store strips any signature and re-signs with a Microsoft
echo certificate. You do not need to buy a code-signing certificate.
echo.
if not defined TESTSIGN (
  echo To install it on THIS machine for a smoke test, re-run:  make_msix.bat %VERSION% testsign
  goto :done
)

rem ==================================================================
rem  6. LOCAL TEST SIGNING - this machine only, never for submission.
rem     Windows refuses to install an unsigned MSIX, so a throwaway
rem     self-signed certificate is needed to smoke-test the package.
rem     The certificate's Subject must equal the manifest's Publisher
rem     string exactly. Nothing here is uploaded anywhere.
rem ==================================================================
set "PFX=msix\codelab-test.pfx"
set "PFXPASS=TESTPASSWORD"
for /f "usebackq delims=" %%p in (`powershell -NoProfile -Command "([xml](Get-Content '%MANIFEST%')).Package.Identity.Publisher"`) do set "PUBLISHER=%%p"
echo [testsign 1/2] Certificate for subject: %PUBLISHER%
if exist "%PFX%" (
  echo   Reusing %PFX%
) else (
  echo   Creating a throwaway certificate in Cert:\CurrentUser\My and exporting it.
  powershell -NoProfile -Command "$c = New-SelfSignedCertificate -Type Custom -KeyUsage DigitalSignature -CertStoreLocation 'Cert:\CurrentUser\My' -TextExtension @('2.5.29.37={text}1.3.6.1.5.5.7.3.3','2.5.29.19={text}') -Subject '%PUBLISHER%' -FriendlyName 'CodeLab Studio MSIX TEST ONLY'; $p = ConvertTo-SecureString -String '%PFXPASS%' -Force -AsPlainText; Export-PfxCertificate -Cert $c -FilePath '%PFX%' -Password $p | Out-Null" || goto :fail
)

echo [testsign 2/2] Signing %PACKAGE% ...
"%SDKBIN%\signtool.exe" sign /fd SHA256 /f "%PFX%" /p %PFXPASS% "%PACKAGE%" || goto :fail

echo.
echo The remaining two steps change machine-wide trust and install the app, so
echo they are NOT run for you. Copy-paste them yourself.
echo.
echo   1^) Trust the test certificate - run in an ELEVATED PowerShell:
echo      $p = ConvertTo-SecureString -String '%PFXPASS%' -Force -AsPlainText
echo      Import-PfxCertificate -CertStoreLocation Cert:\LocalMachine\TrustedPeople -FilePath '%CD%\%PFX%' -Password $p
echo.
echo   2^) Install and smoke-test:
echo      Add-AppxPackage -Path '%CD%\%PACKAGE%'
echo.
echo   When you are done, remove both so the test certificate cannot be abused:
echo      Remove-AppxPackage (Get-AppxPackage *CodeLab* ^| Select -Expand PackageFullName)
echo      Get-ChildItem Cert:\LocalMachine\TrustedPeople ^| Where FriendlyName -like '*CodeLab Studio MSIX TEST ONLY*' ^| Remove-Item
echo.

:done
pause
exit /b 0

:fail
echo.
echo MSIX packaging failed - read the messages above.
pause
exit /b 1
