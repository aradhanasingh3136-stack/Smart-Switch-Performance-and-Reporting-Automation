Attribute VB_Name = "SmartSwitchAutomation"
Option Explicit

' Import this module into SmartSwitch_Reporting.xlsx, then save as .xlsm.
' Supported: desktop Excel. Python launcher uses Windows WScript only.
' The CSV refresh itself uses native Excel and has no COM library dependency.

Private Function RepoRoot() As String
    RepoRoot = Trim$(CStr(ThisWorkbook.Worksheets("Settings").Range("B4").Value2))
    If Len(RepoRoot) = 0 Then Err.Raise vbObjectError + 1, , "Set the repository folder in Settings B4."
    If Right$(RepoRoot, 1) = "/" Or Right$(RepoRoot, 1) = "\" Then RepoRoot = Left$(RepoRoot, Len(RepoRoot) - 1)
End Function

Private Function Q(ByVal text As String) As String
    If InStr(text, Chr$(34)) > 0 Then Err.Raise vbObjectError + 2, , "A configured path contains a quote."
    Q = Chr$(34) & text & Chr$(34)
End Function

Public Sub RunPipelineAndRefresh()
    On Error GoTo Failed
    If InStr(1, Application.OperatingSystem, "Mac", vbTextCompare) > 0 Then
        MsgBox "On Mac run python3 run.py in Terminal, then run RefreshDailyReport.", vbInformation
        Exit Sub
    End If
    Dim launcher As String, result As Long, shell As Object
    launcher = CStr(ThisWorkbook.Worksheets("Settings").Range("B5").Value2)
    If Len(launcher) = 0 Then Err.Raise vbObjectError + 3, , "Set the full python.exe path in Settings B5."
    If Len(Dir$(RepoRoot() & Application.PathSeparator & "run.py")) = 0 Then Err.Raise vbObjectError + 4, , "run.py was not found."
    Set shell = CreateObject("WScript.Shell")
    result = shell.Run(Q(launcher) & " " & Q(RepoRoot() & Application.PathSeparator & "run.py"), 1, True)
    If result <> 0 Then Err.Raise vbObjectError + 5, , "Python failed; report has not been refreshed."
    RefreshDailyReport
    Exit Sub
Failed:
    MsgBox Err.Description, vbExclamation, "SmartSwitch automation"
End Sub

Private Function ReadCsv(ByVal filePath As String, ByVal expectedHeaders As String) As Variant
    Dim source As Workbook, arr As Variant, i As Long, headers As String
    On Error GoTo Failed
    If Len(Dir$(filePath)) = 0 Then Err.Raise vbObjectError + 6, , "Missing CSV: " & filePath
    Workbooks.OpenText Filename:=filePath, Origin:=65001, DataType:=xlDelimited, _
        TextQualifier:=xlTextQualifierDoubleQuote, Comma:=True, Tab:=False, _
        Semicolon:=False, Space:=False, Other:=False, Local:=False, _
        DecimalSeparator:=".", ThousandsSeparator:=",", FieldInfo:=Array(Array(1, xlTextFormat))
    Set source = ActiveWorkbook
    arr = source.Worksheets(1).UsedRange.Value2
    For i = 1 To UBound(arr, 2)
        If i > 1 Then headers = headers & ","
        headers = headers & CStr(arr(1, i))
    Next i
    If headers <> expectedHeaders Then Err.Raise vbObjectError + 7, , "Unexpected CSV headers in " & filePath
    source.Close SaveChanges:=False
    ReadCsv = arr
    Exit Function
Failed:
    Dim message As String
    message = Err.Description
    On Error Resume Next
    If Not source Is Nothing Then source.Close SaveChanges:=False
    On Error GoTo 0
    Err.Raise vbObjectError + 8, , message
End Function

Public Sub RefreshDailyReport()
    Dim oldScreen As Boolean, oldEvents As Boolean, oldCalc As XlCalculation
    Dim daily As Variant, overview As Variant, body() As Variant
    Dim i As Long, j As Long, n As Long, lastRow As Long, sep As String
    Dim ws As Worksheet, message As String, oldData As Variant, oldSettings As Variant
    Dim oldCount As Long, changed As Boolean
    oldScreen = Application.ScreenUpdating: oldEvents = Application.EnableEvents
    oldCalc = Application.Calculation
    On Error GoTo Failed
    sep = Application.PathSeparator
    ' Load and validate both files before changing the report.
    daily = ReadCsv(RepoRoot() & sep & "data" & sep & "processed" & sep & "excel_daily.csv", _
        "date,commands,successes,failures,expected_heartbeats,received_heartbeats,estimated_kwh,baseline_kwh,avg_latency_ms,command_success_rate,heartbeat_delivery_rate")
    overview = ReadCsv(RepoRoot() & sep & "data" & sep & "processed" & sep & "excel_overview.csv", "metric,value")
    n = UBound(daily, 1) - 1
    If n <> 90 Then Err.Raise vbObjectError + 9, , "This workbook template requires the packaged 90-day demo."
    If UBound(overview, 1) <> 5 Then Err.Raise vbObjectError + 10, , "Overview CSV requires four metrics."
    If overview(2, 1) <> "p95_latency_ms" Or overview(3, 1) <> "tariff_inr_per_kwh" _
       Or overview(4, 1) <> "devices" Or overview(5, 1) <> "homes" Then _
        Err.Raise vbObjectError + 11, , "Overview metric order does not match the import contract."
    ReDim body(1 To n, 1 To 9)
    For i = 1 To n
        If Not CStr(daily(i + 1, 1)) Like "####-##-##" Then Err.Raise vbObjectError + 12, , "Invalid date."
        body(i, 1) = DateSerial(CInt(Left$(daily(i + 1, 1), 4)), CInt(Mid$(daily(i + 1, 1), 6, 2)), CInt(Right$(daily(i + 1, 1), 2)))
        For j = 2 To 9
            If Not IsNumeric(daily(i + 1, j)) Then Err.Raise vbObjectError + 13, , "Missing or nonnumeric daily metric."
            body(i, j) = CDbl(daily(i + 1, j))
        Next j
        If body(i, 2) <= 0 Or body(i, 5) <= 0 Or body(i, 3) + body(i, 4) <> body(i, 2) _
            Or body(i, 6) > body(i, 5) Then Err.Raise vbObjectError + 14, , "Daily reconciliation failed."
    Next i
    For i = 2 To 5
        If Not IsNumeric(overview(i, 2)) Then Err.Raise vbObjectError + 15, , "Invalid overview metric."
    Next i
    Set ws = ThisWorkbook.Worksheets("Daily")
    oldData = ws.Range("A6:I95").Value2
    oldSettings = ThisWorkbook.Worksheets("Settings").Range("B7:B12").Value2
    Application.ScreenUpdating = False: Application.EnableEvents = False
    Application.Calculation = xlCalculationManual
    changed = True
    ws.Range("A6:I95").Value2 = body
    With ThisWorkbook.Worksheets("Settings")
        .Range("B7").Value2 = CDbl(overview(3, 2))
        .Range("B8").Value2 = CDbl(overview(2, 2))
        .Range("B9").Value2 = CDbl(overview(4, 2))
        .Range("B10").Value2 = CDbl(overview(5, 2))
        .Range("B12").Value = Now
    End With
    Application.CalculateFull
    ThisWorkbook.Save
    GoTo CleanUp
Failed:
    message = Err.Description
    If changed Then
        On Error Resume Next
        ws.Range("A6:I95").Value2 = oldData
        ThisWorkbook.Worksheets("Settings").Range("B7:B12").Value2 = oldSettings
        On Error GoTo 0
    End If
CleanUp:
    Application.Calculation = oldCalc
    Application.EnableEvents = oldEvents: Application.ScreenUpdating = oldScreen
    If Len(message) > 0 Then
        MsgBox message, vbExclamation, "Refresh failed"
    Else
        MsgBox "90 daily records refreshed and workbook saved.", vbInformation
    End If
End Sub

Public Sub ExportDashboardPDF()
    On Error GoTo Failed
    Dim folder As String, target As String, ws As Worksheet
    folder = ThisWorkbook.Path & Application.PathSeparator & "exports"
    If Len(Dir$(folder, vbDirectory)) = 0 Then MkDir folder
    target = folder & Application.PathSeparator & "SmartSwitch_" & Format$(Now, "yyyymmdd_hhnnss") & ".pdf"
    Set ws = ThisWorkbook.Worksheets("Dashboard")
    With ws.PageSetup
        .PrintArea = "$A$1:$N$35"
        .Orientation = xlLandscape
        .Zoom = False: .FitToPagesWide = 1: .FitToPagesTall = 1
    End With
    ws.ExportAsFixedFormat Type:=xlTypePDF, Filename:=target, Quality:=xlQualityStandard
    MsgBox "Saved: " & target, vbInformation
    Exit Sub
Failed:
    MsgBox Err.Description, vbExclamation, "PDF export failed"
End Sub
