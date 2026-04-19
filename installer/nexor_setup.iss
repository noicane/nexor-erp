; =============================================================
;  NEXOR ERP - Inno Setup Config (Slot Pattern v1.0)
;  -------------------------------------------------------------
;  - Sadece Launcher kurar (200 KB)
;  - ERP versiyonlari sunucudan otomatik indirilir
;  - Bir kere kurulduktan sonra otomatik calisma
; =============================================================

#define MyAppName "Nexor ERP"
#define MyAppPublisher "Redline Creative Solutions"
#define MyAppURL "https://redlinecreative.com"
#define MyAppExeName "NexorLauncher.exe"
#define MyAppVersion "1.0.0"
; Sunucu yolu (gerekirse degistir, registry'ye yazilir)
; IP kullaniliyor - VPN'de de calismasi icin (hostname VPN'de cozulmuyor)
#define MyServerPath "\\192.168.10.35\atmo_logic\releases"

[Setup]
AppId={{B4A2E91D-3F47-4D8C-9E5B-1A6F0D2C7E89}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\Nexor
DefaultGroupName=Nexor ERP
DisableProgramGroupPage=yes
OutputDir={#SourcePath}..\dist\installer
OutputBaseFilename=NexorSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; PrivilegesRequired=lowest: admin gerek yok, per-user install (%LOCALAPPDATA%\Programs\Nexor)
; Uyari: admin + per-user data karisikligi yok artik
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile={#SourcePath}..\assets\icon.ico
; ---- Code Signing (sertifika gelince acilacak) ----
; SignTool=signtool $f
; SignedUninstaller=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaustune kisayol olustur"; GroupDescription: "Ek kisayollar:"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "Hizli baslat menusune ekle"; GroupDescription: "Ek kisayollar:"; Flags: unchecked

[Files]
; Launcher exe (onefile build - PyInstaller cikti)
Source: "{#SourcePath}..\dist\NexorLauncher.exe"; DestDir: "{app}"; Flags: ignoreversion

; Icon (kisayollar icin)
Source: "{#SourcePath}..\assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Nexor ERP"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\Nexor ERP'yi Kaldir"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Nexor ERP"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Nexor ERP"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: quicklaunchicon

[Registry]
; Launcher'in sunucu yolunu okuyabilmesi icin
Root: HKCU; Subkey: "Software\Nexor"; Flags: uninsdeletekeyifempty
Root: HKCU; Subkey: "Software\Nexor"; ValueType: string; ValueName: "ServerPath"; ValueData: "{#MyServerPath}"; Flags: uninsdeletevalue

[Dirs]
; Lokal slot ve log klasorleri (kullanici izni ile, admin gerek yok)
Name: "{localappdata}\Nexor\releases"
Name: "{localappdata}\Nexor\logs"

[Run]
; Kurulum sonrasi launcher'i baslat (kullanici isterse)
Filename: "{app}\{#MyAppExeName}"; Description: "Nexor ERP'yi simdi calistir"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Sadece Program Files'taki launcher silinir
; %LOCALAPPDATA%\Nexor (kullanici verisi + slot cache) BIRAKILIR
; Tamamen temizlemek isteyen kullanici manuel siler
Type: filesandordirs; Name: "{app}"

[Code]
{ ============================================================
  Kurulum oncesi: Eski kurulumlari kontrol et
  ============================================================ }

function InitializeSetup(): Boolean;
var
  Uninstaller: String;
  ResultCode: Integer;
begin
  Result := True;

  { Eski Nexor kurulumu varsa kullaniciya sor }
  if RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{{B4A2E91D-3F47-4D8C-9E5B-1A6F0D2C7E89}_is1', 'UninstallString', Uninstaller) then
  begin
    if MsgBox('Onceki Nexor kurulumu tespit edildi.' + #13#10 +
              'Once eski versiyonu kaldirip devam edelim mi?',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      Uninstaller := RemoveQuotes(Uninstaller);
      Exec(Uninstaller, '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  LocalAppData: String;
begin
  if CurStep = ssPostInstall then
  begin
    { Lokal cache klasoru kullanicinin kullanabilecegi sekilde olusturulur }
    LocalAppData := ExpandConstant('{localappdata}\Nexor');
    ForceDirectories(LocalAppData + '\releases');
    ForceDirectories(LocalAppData + '\logs');
  end;
end;
