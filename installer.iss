[Setup]
AppName=Lua AI Studio
AppVersion=1.1
AppPublisher=Lua AI Studio Contributors
AppPublisherURL=https://github.com/yourusername/lua-ai-studio
AppURL=https://github.com/yourusername/lua-ai-studio
DefaultDirName={autopf}\LuaAIStudio
DefaultGroupName=Lua AI Studio
OutputDir=dist\installer
OutputBaseFilename=LuaAIStudio-Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=app\ui\resources\icon.ico
LicenseFile=LICENSE
AllowNoIcons=yes
PrivilegesRequired=none
ArchitecturesInstallIn64BitMode=x64
DisableWelcomePage=no
AlwaysShowDirOnReadyPage=yes
ShowTasksAtTop=yes
WizardSizePercent=125
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunch"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenu"; Description: "Create Start Menu shortcuts"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checked

[Files]
Source: "dist\lua_ai_studio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\models"
Name: "{app}\projects"

[Icons]
Name: "{group}\Lua AI Studio"; Filename: "{app}\lua_ai_studio.exe"; Comment: "Lua AI Studio with integrated AI"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,Lua AI Studio}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Lua AI Studio"; Filename: "{app}\lua_ai_studio.exe"; Tasks: desktopicon; Comment: "Lua AI Studio"; WorkingDir: "{app}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Lua AI Studio"; Filename: "{app}\lua_ai_studio.exe"; Tasks: quicklaunch; Comment: "Lua AI Studio"; WorkingDir: "{app}"

[Run]
Filename: "{app}\lua_ai_studio.exe"; Description: "{cm:LaunchProgram,Lua AI Studio}"; Flags: nowait postinstall skipifsilent; Parameters: "--debug"

[UninstallDelete]
Type: dirifempty; Name: "{app}"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    MsgBox('✓ Lua AI Studio has been installed successfully!' + #13#13 +
           '📦 First launch will download the AI model (~2-7GB).' + #13 +
           '⏱️  Download time depends on your internet connection:' + #13 +
           '   • 1.5B model: ~3-5 minutes' + #13 +
           '   • 7B model: ~10-15 minutes' + #13#13+
           'Ready to use! Check Start Menu for shortcuts.', mbInformation, MB_OK);
end;
