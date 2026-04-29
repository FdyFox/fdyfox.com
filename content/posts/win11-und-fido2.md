---
date: '2026-04-24T00:01:25+02:00'
draft: false
title: 'Windows 11 und FIDO2: Standard-Gerät auf Hardware-Key setzen'
tags: ["windows", "fido2", "sicherheit", "powershell", "tipps"]
---

Für alle, denen es auf die Nerven geht, dass Windows 11 bei der Abfrage eines Hardware-Security-Keys standardmäßig immer "iPhone, iPad oder Android-Gerät" vorauswählt - habt ihr eine Lösung gefunden?

Ich habe Dinge wie das hier versucht - leider ohne Erfolg:

```powershell {title="Set GPO via Powershell"}
# Create registry key
New-Item -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\SecondaryAuthenticationFactor" -Force

# Set property
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\SecondaryAuthenticationFactor" `
  -Name "AllowSecondaryAuthenticationDevice" -Value 0 -Type DWord -Force

# Check result
Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\SecondaryAuthenticationFactor"
```

oder aber auch:

```cmd {title="Disable FIDO2"}
# FIDO2-Sicherheitsschlüssel deaktivieren
reg add "HKLM\SOFTWARE\Policies\Microsoft\FIDO" /v EnableFIDODeviceLogon /t REG_DWORD /d 0 /f
```

Beides scheint nicht zu funktionieren... warum auch immer... **Lösung gesucht!**

Nachdem ich mich noch eine Weile mit dem Thema beschäftigt habe, bin ich auf folgendes Tool gestoßen: [AuthenticatorChooser](https://github.com/Aldaviva/AuthenticatorChooser)

Das kleine Tool klickt den Dialog im Hintergrund quasi automatisch weg - kein echter Fix, aber es funktioniert. Schön ist was anderes, ein zusätzliches Drittanbieter-Programm für sowas zu brauchen... aber gut.
