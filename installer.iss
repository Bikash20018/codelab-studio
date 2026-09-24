; Inno Setup 6.3+  ->  creates the versioned CodeLabStudio installer.
; Run build.bat first so dist\CodeLabStudio exists (with mingw64 inside).

#define AppName "CodeLab Studio"
#define AppVersion "2.1.0"
#define AppExe "CodeLabStudio.exe"
#ifndef SourceDir
  #define SourceDir "dist\CodeLabStudio"
#endif

[Setup]
AppId={{8F3C2A51-6B7D-4E1A-9C55-2D7B1E0A4C93}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Bikash Chhetri
AppPublisherURL=https://www.bikashchhetri.com.np
AppSupportURL=https://www.bikashchhetri.com.np
DefaultDirName={autopf}\CodeLab Studio
DefaultGroupName=CodeLab Studio
UninstallDisplayIcon={app}\{#AppExe}
OutputDir=installer
OutputBaseFilename=CodeLabStudio-Setup-{#AppVersion}
SetupIconFile=assets\app.ico
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; "commandline" is what makes /ALLUSERS and /CURRENTUSER work.  The Microsoft
; Store runs this installer silently, where a per-machine install would need a
; UAC prompt nobody can answer, so /CURRENTUSER has to be accepted.
PrivilegesRequiredOverridesAllowed=commandline dialog
ChangesAssociations=yes
VersionInfoVersion={#AppVersion}
VersionInfoCompany=Bikash Chhetri
VersionInfoProductName={#AppName}
VersionInfoDescription={#AppName} Setup

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "assoc"; Description: "Add CodeLab Studio to ""Open with"" for .c and .cpp files"; GroupDescription: "Files:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\CodeLabStudio.Source"; ValueType: string; ValueName: ""; ValueData: "C/C++ Source File"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\CodeLabStudio.Source\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExe},0"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\CodeLabStudio.Source\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.c\OpenWithProgids"; ValueType: string; ValueName: "CodeLabStudio.Source"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.cpp\OpenWithProgids"; ValueType: string; ValueName: "CodeLabStudio.Source"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
