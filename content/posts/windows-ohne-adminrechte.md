---
title: "Windows ohne Adminrechte: Schriften und AD-Cmdlets durch die Hintertür"
date: 2026-10-30T08:00:00+01:00
tags: ["windows", "powershell", "tipps"]
draft: false
---

Firmen-Laptop, keine Adminrechte, alles per GPO zugenagelt. Kennt man. Aber zugenagelt heißt bei Windows selten *dicht* - oft ist nur die bequeme Tür abgeschlossen, und das Fenster daneben steht sperrangelweit offen. Zwei solcher Fenster nutze ich regelmäßig: Schriften installieren, obwohl "Installieren" gesperrt ist, und AD-Cmdlets nutzen, obwohl RSAT fehlt.

> [!NOTE]
> Alles hier läuft mit ganz normalen Benutzerrechten - keine Exploits, keine Rechteausweitung. Ob eure IT das lustig findet, steht auf einem anderen Blatt. Ihr wisst, was ihr tut.

## Hack 1: Schriften installieren, wenn "Installieren" gesperrt ist

Rechtsklick auf die `.ttf`, **"Installieren"** - und Windows meldet, das sei **keine gültige Schriftdatei**. Ist es natürlich doch, auf jedem anderen Rechner lässt sie sich problemlos installieren. Die Meldung ist schlicht irreführend, dahinter steckt die GPO. An `C:\Windows\Fonts` kommt man ohne Admin sowieso nicht ran - also Pech gehabt?

Nicht ganz.

### Das offene Fenster

Seit Windows 10 1809 gibt es neben dem systemweiten Schriftordner auch einen **pro Benutzer**. Er liegt im eigenen Profil, Schreibrechte hat man dort also immer:

```text
%LOCALAPPDATA%\Microsoft\Windows\Fonts
```

Die passenden Registry-Einträge landen entsprechend nicht unter `HKLM`, sondern unter `HKCU` - ebenfalls ohne Adminrechte beschreibbar:

```text
HKCU\Software\Microsoft\Windows NT\CurrentVersion\Fonts
```

Genau dorthin installiert Windows eine Schrift auch selbst, wenn man ohne Adminrechte auf "Installieren" klickt. Die Sperre greift aber nur beim Installieren über den Explorer - Ordner und Registry-Schlüssel bleiben beschreibbar. Also erledigen wir die beiden Schritte eben selbst: Datei in den Ordner kopieren, Registry-Eintrag anlegen. Nur die Datei zu kopieren reicht nicht - ohne Eintrag in der Registry lädt Windows die Schrift nicht.

### Das Skript

Registry-Einträge von Hand zu tippen ist was für Masochisten. Also ein Skript: Es schnappt sich alle `.ttf`, `.otf` und `.ttc` im Benutzer-Schriftordner, trägt fehlende in die Registry ein und schiebt sie per Win32-API direkt in die laufende Sitzung. Abmelden ist in der Regel nicht nötig, ein Ticket schon gar nicht.

```powershell {title="install_fonts_user.ps1"}
<#
.SYNOPSIS
    Registers all fonts in the per-user font folder (no admin rights needed).

.DESCRIPTION
    Copy .ttf/.otf/.ttc files to %LOCALAPPDATA%\Microsoft\Windows\Fonts and run
    this script. Every font that is not yet registered in
    HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts gets an entry and is
    loaded into the current session, so a logout is usually not necessary.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File install_fonts_user.ps1
#>

$ErrorActionPreference = 'Stop'

$fontDir = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
$regPath = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'

if (-not (Test-Path $fontDir)) {
    Write-Host "Font folder $fontDir does not exist. Nothing to do." -ForegroundColor Yellow
    exit 0
}

if (-not (Test-Path $regPath)) {
    New-Item -Path $regPath -Force | Out-Null
}

# Win32 helpers to load fonts without logout. Fails in Constrained Language Mode.
$canLoad = $true
try {
    Add-Type -Namespace Win32 -Name FontApi -MemberDefinition @'
[DllImport("gdi32.dll", CharSet = CharSet.Unicode)]
public static extern int AddFontResource(string lpFileName);
[DllImport("user32.dll", CharSet = CharSet.Unicode)]
public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam, uint fuFlags, uint uTimeout, out IntPtr lpdwResult);
'@
} catch {
    $canLoad = $false
    Write-Host "Cannot load Win32 API (policy?). Fonts will be available after logout/login." -ForegroundColor Yellow
}

# Font name for the registry entry (only a label, Windows reads the real name from the file)
function Get-FontName([System.IO.FileInfo]$file) {
    try {
        Add-Type -AssemblyName System.Drawing
        $collection = New-Object System.Drawing.Text.PrivateFontCollection
        $collection.AddFontFile($file.FullName)
        $name = $collection.Families[0].Name
        $collection.Dispose()
        if ($name) { return $name }
    } catch {
        # GDI+ can not read CFF based .otf files -> fall back to the file name
    }
    return $file.BaseName
}

# Already registered files (values can be a full path or only a file name)
$registered = @{}
$props = Get-ItemProperty -Path $regPath
foreach ($p in $props.PSObject.Properties) {
    if ($p.Name -like 'PS*') { continue }
    $registered[(Split-Path ([string]$p.Value) -Leaf).ToLowerInvariant()] = $true
}

$fonts = Get-ChildItem -Path $fontDir -File |
    Where-Object { $_.Extension -match '^\.(ttf|otf|ttc)$' }

$installed = 0
foreach ($font in $fonts) {
    if ($registered.ContainsKey($font.Name.ToLowerInvariant())) {
        Write-Host "Skipping $($font.Name) (already registered)"
        continue
    }

    $type = if ($font.Extension -eq '.otf') { 'OpenType' } else { 'TrueType' }
    $regName = "$(Get-FontName $font) ($type)"

    New-ItemProperty -Path $regPath -Name $regName -Value $font.FullName `
        -PropertyType String -Force | Out-Null

    if ($canLoad) {
        [Win32.FontApi]::AddFontResource($font.FullName) | Out-Null
    }

    Write-Host "Installed $($font.Name) as '$regName'" -ForegroundColor Green
    $installed++
}

# Tell running applications that the font list changed (WM_FONTCHANGE)
if ($canLoad -and $installed -gt 0) {
    $result = [IntPtr]::Zero
    [Win32.FontApi]::SendMessageTimeout([IntPtr]0xffff, 0x1D, [IntPtr]::Zero, [IntPtr]::Zero, 2, 1000, [ref]$result) | Out-Null
}

Write-Host "Done: $installed new font(s) registered." -ForegroundColor Cyan
if ($installed -gt 0) {
    Write-Host "Restart running applications to use the new fonts. If a font is still missing, log out and back in."
    Write-Host ""
    Write-Host "Browsers often keep running in the background. Restart them completely with:"
    Write-Host "  Chrome:  chrome://restart"
    Write-Host "  Edge:    edge://restart"
    Write-Host "  Brave:   brave://restart"
    Write-Host "  Vivaldi: vivaldi://restart"
    Write-Host "  Firefox: close all windows (about:profiles -> 'Restart normally...')"
}
```

#### Was passiert unter der Haube?

- **Registry-Eintrag:** Pro Datei ein Wert `Schriftname (TrueType)` → voller Pfad. Der Name ist eigentlich nur Deko, Windows liest den echten Namen aus der Datei. Das Skript fragt trotzdem höflich bei `System.Drawing` nach. CFF-basierte `.otf` mag GDI+ nicht - dann muss halt der Dateiname herhalten.
- **Idempotent:** Schon registrierte Dateien werden übersprungen. Neue Schriften reinwerfen, Skript nochmal laufen lassen, fertig.
- **Ohne Abmelden:** `AddFontResource` aus der `gdi32.dll` lädt die Schrift sofort, danach geht ein `WM_FONTCHANGE`-Broadcast an alle Fenster: "Hey, es gibt neue Schriften."
- **Plan B:** Hat die IT PowerShell in den *Constrained Language Mode* gesperrt (AppLocker/WDAC), ist `Add-Type` mit eigenem C# tabu. Dann wird trotzdem registriert - die Schrift taucht eben erst nach dem nächsten Abmelden auf.

### So geht's

1. `%LOCALAPPDATA%\Microsoft\Windows\Fonts` in die Explorer-Adresszeile werfen. Ordner nicht da? Anlegen.
2. Schriften reinkopieren.
3. Skript abfeuern:

```powershell {title="Skript ausführen"}
powershell -ExecutionPolicy Bypass -File install_fonts_user.ps1
```

`-ExecutionPolicy Bypass` gilt nur für diesen einen Aufruf - die Execution Policy ist bekanntlich keine Sicherheitsgrenze, sondern eher ein freundlicher Hinweis. Ist sie per GPO festgenagelt, greift der Parameter nicht. Dann den Skriptinhalt einfach direkt in eine offene PowerShell-Sitzung pasten.

Danach die Programme neu starten. Achtung bei Browsern: Chrome, Edge & Co. leben gern als Zombie im Hintergrund weiter. `chrome://restart` bzw. `edge://restart` killt sie ordentlich - das Skript spuckt die passenden Befehle am Ende auch aus.

### Wieder loswerden

Eintrag unter `HKCU\Software\Microsoft\Windows NT\CurrentVersion\Fonts` löschen, Datei aus dem Ordner werfen. Ist die Schrift noch geladen, klappt das Löschen der Datei eventuell erst nach dem Abmelden.

### Haken an der Sache

Benutzer-Schriften sieht nur der eigene Benutzer - für fast alles reicht das. Ein paar Dinosaurier-Anwendungen schauen allerdings stur nur in `C:\Windows\Fonts`. Da hilft dann nur noch ein Ticket.

## Hack 2: AD-Cmdlets ohne RSAT

Mal eben gucken, in welchen AD-Gruppen man steckt oder welche Domain Controller rumstehen? `Get-ADUser`: *"The term is not recognized..."*. Klar, die Cmdlets kommen mit **RSAT**, und RSAT installieren braucht - richtig - Admin.

Brauchen wir aber gar nicht. Das ganze `ActiveDirectory`-Modul ist im Kern eine einzige DLL: `Microsoft.ActiveDirectory.Management.dll`. Und eine DLL kann man einfach importieren - ganz ohne Installation.

### Die DLL organisieren

Die saubere Variante: Von einem Rechner mit RSAT klauen, äh, kopieren. Sie liegt im Global Assembly Cache:

```text
C:\Windows\Microsoft.NET\assembly\GAC_64\Microsoft.ActiveDirectory.Management\
```

Die schnelle Variante: [Download bei dllme.com](https://www.dllme.com/dll/files/microsoft_activedirectory_management).

> [!WARNING]
> DLLs von irgendwelchen Download-Seiten sind russisches Roulette - ihr ladet fremden Code in eure Session, und der läuft mit euren Rechten in der Domäne. Mindestens die digitale Signatur checken (Rechtsklick → Eigenschaften → Digitale Signaturen → Microsoft). Besser: selbst von einer RSAT-Maschine holen.

### Laden und loslegen

Kommt die DLL aus dem Internet, erst den "aus dem Internet"-Stempel entfernen. Dann importieren - und zwar mit Pfad, sonst sucht PowerShell nur in den Modulordnern und findet nix:

```powershell {title="AD-Cmdlets ohne RSAT"}
# Unblock the file
gci .\Microsoft.ActiveDirectory.Management.dll | Unblock-File

# Import the Module -> Use the full path
Import-Module "$pwd\Microsoft.ActiveDirectory.Management.dll"

# Get all commands
Get-Command -Module Microsoft.ActiveDirectory.Management

# Get AD-User
$user = [Environment]::UserName
$domain = [Environment]::UserDomainName

# Get user data
Get-ADUser $user

# Get all User Groups
Get-ADPrincipalGroupMembership $user -ResourceContextServer $domain

# Get user groups -> only names
(Get-ADPrincipalGroupMembership $user -ResourceContextServer $domain).SamAccountName

# Get all DCs
(Get-ADForest).Domains | %{ Get-ADDomainController -Filter * -Server $_ }
```

`Get-Command` zeigt, was man bekommen hat: praktisch alles, was das echte `ActiveDirectory`-Modul auch kann.

### Und was darf man damit?

Mehr als man denkt. Die Cmdlets laufen mit euren normalen Rechten - aber im AD darf standardmäßig jeder authentifizierte Benutzer erstaunlich viel *lesen*: Benutzer, Gruppen, Mitgliedschaften, Computer, DCs. Schreiben nur dort, wo ihr eh dürft. Die DLL ist kein Generalschlüssel, sie spart nur die RSAT-Installation.

### Wenn's klemmt

- **"Unable to contact the server":** Die Cmdlets reden nicht LDAP, sondern mit den Active Directory Web Services (ADWS) auf TCP-Port **9389**. Ist der zu, ist hier Schluss.
- **Import schlägt fehl:** AppLocker oder WDAC blockieren das Laden nicht freigegebener DLLs. Die Execution Policy dagegen interessiert sich für DLLs nicht die Bohne.
