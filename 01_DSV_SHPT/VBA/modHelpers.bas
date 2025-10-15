Attribute VB_Name = "modHelpers"
Option Explicit
'==========================
' Module: modHelpers
' Desc: 공용 헬퍼, 로깅, 환경 제어 유틸리티
'==========================

Public Sub LogAction(ByVal tag As String, ByVal msg As String)
    Dim wsLog As Worksheet, nr As Long
    On Error Resume Next
    Set wsLog = ThisWorkbook.Worksheets("LOG")
    If wsLog Is Nothing Then
        Set wsLog = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        wsLog.Name = "LOG"
        wsLog.Range("A1:D1").Value = Array("TIMESTAMP", "TAG", "MESSAGE", "USER")
        wsLog.Rows(1).Font.Bold = True
    End If
    On Error GoTo 0
    
    With wsLog
        nr = .Cells(.Rows.Count, 1).End(xlUp).Row + 1
        .Cells(nr, 1).Value = Now
        .Cells(nr, 2).Value = tag
        .Cells(nr, 3).Value = msg
        .Cells(nr, 4).Value = Environ$("Username")
    End With
End Sub

Public Sub LogActionSafe(ByVal tag As String, ByVal msg As String)
    On Error Resume Next
    LogAction tag, msg
    If Err.Number <> 0 Then
        Debug.Print Now, tag, msg
        Err.Clear
    End If
    On Error GoTo 0
End Sub

Public Sub AppBegin(ByVal tag As String)
    On Error Resume Next
    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.Calculation = xlCalculationManual
    Application.DisplayStatusBar = True
    Application.StatusBar = "Running: " & tag & " ..."
    On Error GoTo 0
End Sub

Public Sub AppEnd()
    On Error Resume Next
    Application.ScreenUpdating = True
    Application.EnableEvents = True
    Application.Calculation = xlCalculationAutomatic
    Application.StatusBar = False
    On Error GoTo 0
End Sub

Public Function SafeFind(ByVal ws As Worksheet, ByVal whatText As String, _
                         ByVal exactMatch As Boolean, Optional ByVal inRange As Range) As Range
    Dim findRng As Range, lookAtMode As XlLookAt
    On Error Resume Next
    If inRange Is Nothing Then Set findRng = ws.UsedRange Else Set findRng = inRange
    On Error GoTo 0
    If findRng Is Nothing Then Exit Function
    
    lookAtMode = IIf(exactMatch, xlWhole, xlPart)
    Set SafeFind = findRng.Find(What:=whatText, After:=findRng.Cells(1, 1), LookIn:=xlValues, _
                                LookAt:=lookAtMode, SearchOrder:=xlByRows, _
                                SearchDirection:=xlNext, MatchCase:=False)
End Function

Public Function lastDataRow(ByVal ws As Worksheet, ByVal col As Long) As Long
    If col <= 0 Then
        lastDataRow = 0
        Exit Function
    End If
    
    If Application.WorksheetFunction.CountA(ws.Columns(col)) = 0 Then
        lastDataRow = 0
    Else
        lastDataRow = ws.Cells(ws.Rows.Count, col).End(xlUp).Row
    End If
End Function

Public Sub ClearRange(ByVal target As Range)
    If target Is Nothing Then Exit Sub
    On Error Resume Next
    target.ClearContents
    On Error GoTo 0
End Sub

Public Function ProcExists(ByVal ProcName As String) As Boolean
    On Error Resume Next
    Application.Run ProcName
    Select Case Err.Number
        Case 0: ProcExists = True
        Case 1004, 438: ProcExists = False
        Case Else: ProcExists = True
    End Select
    Err.Clear
    On Error GoTo 0
End Function

Public Function GetOrCreateSheet(ByVal sheetName As String) As Worksheet
    On Error Resume Next
    Set GetOrCreateSheet = ThisWorkbook.Worksheets(sheetName)
    If Err.Number <> 0 Then
        Err.Clear
        Set GetOrCreateSheet = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        GetOrCreateSheet.Name = sheetName
    End If
    On Error GoTo 0
End Function

Public Function Nz(ByVal v As Variant, Optional ByVal defaultValue As Double = 0#) As Double
    If IsError(v) Then
        Nz = defaultValue
    ElseIf IsNumeric(v) Then
        If Not IsEmpty(v) And Not IsNull(v) Then Nz = CDbl(v) Else Nz = defaultValue
    Else
        Nz = defaultValue
    End If
End Function

