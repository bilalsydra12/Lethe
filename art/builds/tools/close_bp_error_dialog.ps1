# Answers Unreal's "Blueprint Asset Compilation Error(s)" prompt with its first button, "Play in Editor", so an
# unattended movie render continues. (The MetaHuman's Live Link face blueprint fails to compile after every rebuild;
# stills don't use it.) Closing the window instead cancels the render. Usage: close_bp_error_dialog.ps1 [-Minutes 30]
param([int]$Minutes = 30)
Add-Type @'
using System; using System.Text; using System.Collections.Generic; using System.Runtime.InteropServices;
public class BpDlg2 { delegate bool P(IntPtr h, IntPtr l);
[DllImport("user32.dll")] static extern bool EnumWindows(P p, IntPtr l);
[DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
[DllImport("user32.dll")] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
[DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
public static List<IntPtr> Find(int[] pids, string title) { var o = new List<IntPtr>();
 EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p);
  if (Array.IndexOf(pids, (int)p) >= 0 && IsWindowVisible(h)) { var sb = new StringBuilder(256); GetWindowText(h, sb, 256);
   if (sb.ToString().Contains(title)) o.Add(h); } return true; }, IntPtr.Zero); return o; } }
'@
$sh = New-Object -ComObject WScript.Shell
$end = (Get-Date).AddMinutes($Minutes)
while ((Get-Date) -lt $end) {
    $pids = [int[]]@(Get-Process UnrealEditor -EA SilentlyContinue | % { $_.Id })
    if ($pids.Count -gt 0) {
        foreach ($h in [BpDlg2]::Find($pids, 'Compilation Error')) {
            [BpDlg2]::SetForegroundWindow($h) | Out-Null
            Start-Sleep -Milliseconds 400
            if ([BpDlg2]::GetForegroundWindow() -eq $h) {
                $sh.SendKeys('+{TAB}'); Start-Sleep -Milliseconds 300; $sh.SendKeys('{ENTER}')    # focus starts on Cancel
                "pressed Play in Editor on $h at $(Get-Date -f HH:mm:ss)"
            } else { "dialog $h is not in front yet" }
        }
    }
    Start-Sleep 4
}
